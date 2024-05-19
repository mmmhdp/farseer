import multiprocessing as mp
import threading
import os
import signal

import cv2
import numpy.typing as npt

from broker.broker_service import Broker
from runner_models import Event
from db.db_service import ProcessCacheDatabase, ImgS3Database
from logger import log

INVALID_FRAMES_BEFORE_INTERRUPTION = 50
PREDICT_ON_GAP = 100
if INVALID_FRAMES_BEFORE_INTERRUPTION > PREDICT_ON_GAP:
    raise ValueError(
        f"Ivalid gap for frames consumption, before break of invalid: {INVALID_FRAMES_BEFORE_INTERRUPTION} > gap: {PREDICT_ON_GAP}")

CONSUMER_TOPICS = ["api_runner"]


class RunnerService():

    def __init__(self, topics=CONSUMER_TOPICS):
        self.msg_broker = Broker(topics=topics)

    def read_and_process_event(self):
        event: Event = self.msg_broker.consume_event()

        if not event:
            return

        log.debug(f"get event: {event.request_uuid}")

        self._update_stream_reading_with_event(event)

    def _update_stream_reading_with_event(self, event: Event) -> None:
        log.info(
            f"start to process event: {event.event} with uuid:{event.request_uuid}")

        event_type = event.event

        match event_type:
            case "start":
                self.msg_broker.publish_event(
                    event=event, topic="runner_fsm_st", state="in_startup_processing")

                event_pr = mp.Process(
                    target=self._read_stream,
                    args=((event,)),
                    daemon=True
                )
                event_pr.start()

                log.debug(
                    f"start processing for event: {event.request_uuid} with pid: {event_pr.pid}")

                self.__save_worker_pid(event_pr.pid, event)

            case "stop":
                event_th = threading.Thread(
                    target=self._stop_stream_reading,
                    args=((event,)),
                    daemon=True
                )
                log.debug(
                    f"start processing for event: {event.request_uuid} with thread with pid: {event_th}")
                event_th.start()

    def _read_stream(self, event: Event) -> None:
        try:
            vid = cv2.VideoCapture(event.stream_source)
            log.debug(
                f"start reading stream for event: {event.request_uuid} and vid: {vid}")

            corrupted_frames = 0
            frames = 0

            while True:
                ret, frame = vid.read()

                if frame is None:
                    corrupted_frames += 1
                    if corrupted_frames == INVALID_FRAMES_BEFORE_INTERRUPTION:
                        log.warning(
                            "stream reading loop is exited because of invalid stream source")
                        self._stop_stream_reading(event)
                        break
                    continue

                frames += 1

                if frames == PREDICT_ON_GAP:
                    corrupted_frames = 0

                    frame_id = self.__save_frame(frame, event)

                    self.__publish_event_for_inference(event, frame_id)

                    frames = 0
                    break

            vid.release()

        except Exception as ex:
            log.critical(f"stop reading stream because of ex: {ex}")

    def __publish_event_for_fsm_stenographer_about_invalid_stream_source(self, event: Event):
        _producer = self.__get_producer()
        event_for_inference = Event(
            event="invalid_source",
            state="",
            stream_source=event.stream_source,
            request_uuid=event.request_uuid,
        )

        _producer.publish_event(
            event=event_for_inference,
            topic="runner_fsm_st",
            state="inactive",
        )

    def __get_producer(self):
        return Broker(producer_only=True)

    def __publish_event_for_inference(self, event: Event, frame_id):
        topic = "runner_inference"
        state = "active"

        log.debug(f"""try to publish event: {event.event}
        with uuid: {event.request_uuid}
        topic: {topic}
        with previous state: {event.state}
        event: {event.event}
        stream_source: {event.stream_source}
         """)

        try:
            _producer = self.__get_producer()
            event_for_inference = Event(
                event="predict",
                state="",
                stream_source=frame_id,
                request_uuid=event.request_uuid,
            )

            _producer.publish_event(
                event=event_for_inference,
                topic=topic,
                state=state,
            )

        except Exception as ex:
            log.error(
                f"""failed to publish event: {event.event}
                with event_uuid: {event.request_uuid}
                because of exception: {ex}""")

    def __save_frame(self, frame: npt.ArrayLike, event: Event):
        _img_db = ImgS3Database()
        frame_id = _img_db.save_frame(frame, event)
        return frame_id

    def __save_worker_pid(self, pid: int, event: Event):
        cache_db = ProcessCacheDatabase()
        cache_db.save_pid(pid, event)

    def _stop_stream_reading(self, event: Event):
        log.info(f"start to stop event: {event.request_uuid}")

        cache_db = ProcessCacheDatabase()
        is_exists = cache_db.is_exists(event)

        if not is_exists:
            log.critical(
                f"can't find pid for event: {event.request_uuid}")
            return

        log.debug(
            f"before main actions of deletion for event: {event.request_uuid}")

        self.__publish_event_for_fsm_stenographer_about_in_shutdown_processing(
            event)
        self.__kill_stream_processes(event)
        self.__clear_cache_db(event)
        self.__clear_image_storage(event)
        self.__publish_event_for_fsm_stenographer_about_is_inactive(
            event)

        log.info(f"stream stopped for event: {event.request_uuid}")

    def __publish_event_for_fsm_stenographer_about_is_inactive(
            self, event: Event):
        topic = "runner_fsm_st"
        state = "inactive"
        event.event = "shut_down"

        log.debug(f"""try to publish event: {event.event}
        with uuid: {event.request_uuid}
        topic: {topic}
        with previous state: {event.state}
        event: {event.event}
        stream_source: {event.stream_source}
         """)
        try:
            _producer = self.__get_producer()
            event_for_inference = Event(
                event=event.event,
                state="",
                stream_source=event.stream_source,
                request_uuid=event.request_uuid,
            )

            _producer.publish_event(
                event=event_for_inference,
                topic=topic,
                state=state,
            )
        except Exception as ex:
            log.error(
                f"""failed to publish event: {event.event}
                with event_uuid: {event.request_uuid}
                because of exception: {ex}""")

    def __publish_event_for_fsm_stenographer_about_in_shutdown_processing(self, event: Event):
        topic = "runner_fsm_st"
        state = "init_shut_down"
        event.event = "shut_down"

        log.debug(f"""try to publish event: {event.event}
        with uuid: {event.request_uuid}
        topic: {topic}
        with previous state: {event.state}
        event: {event.event}
        stream_source: {event.stream_source}
         """)
        try:
            _producer = self.__get_producer()
            event_for_inference = Event(
                event=event.event,
                state="",
                stream_source=event.stream_source,
                request_uuid=event.request_uuid,
            )

            _producer.publish_event(
                event=event_for_inference,
                topic=topic,
                state=state,
            )
        except Exception as ex:
            log.error(
                f"""failed to publish event: {event.event}
                with event_uuid: {event.request_uuid}
                because of exception: {ex}""")

    def __kill_stream_processes(self, event: Event):
        cache_db = ProcessCacheDatabase()
        pids = cache_db.find_all_possible_pids_for_event(event)
        for pid in pids:
            os.kill(pid, signal.SIGTERM)
        log.info(
            f"processes with pids {pids} for event : {event.request_uuid} are killed")

    def __clear_cache_db(self, event: Event):
        log.debug(f"before processes db clean for event:{event.request_uuid}")
        cache_db = ProcessCacheDatabase()
        cache_db.clear_after_event(event)

    def __clear_image_storage(self, event):
        log.debug(f"before image clean for event:{event.request_uuid}")
        _img_db = ImgS3Database()
        _img_db.clear_after_event(event)


runner_service = RunnerService()
