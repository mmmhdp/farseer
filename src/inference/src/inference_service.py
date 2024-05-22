import threading
import json

from ultralytics import YOLO
import numpy.typing as npt

from broker.broker_service import Broker
from inference_models import Event
from db.db_service import PredCacheDatabase, ImgS3Database
from logger import log


CONSUMER_TOPICS = ["runner_inference"]


class InferenceService():

    def __init__(self, topics=CONSUMER_TOPICS):
        self.msg_broker = Broker(topics=topics)

    def read_and_process_event(self):
        event: Event = self.msg_broker.consume_event()

        if not event:
            return

        log.debug(f"get event: {event.request_uuid}")

        self._process_event(event)

    def _process_event(self, event: Event) -> None:
        log.info(
            f"start to process event: {event.event} with uuid:{event.request_uuid}")

        event_type = event.event

        match event_type:
            case "predict":
                self.msg_broker.publish_event(
                    event=event, topic="inference_fsm_st", state="active")

                event_th = threading.Thread(
                    target=self._predict,
                    args=((event,)),
                    daemon=True
                )
                event_th.start()

                log.debug(
                    f"start processing for event {event_type} with: {event.request_uuid}")

            case "clean_up":
                event_th = threading.Thread(
                    target=self.__clear_cache_db,
                    args=((event,)),
                    daemon=True
                )
                event_th.start()

                log.debug(
                    f"start processing for event {event_type} with: {event.request_uuid}")

            case _:
                log.warning(f"not implemented event_type: {event_type}")

    def _predict(self, event: Event):
        model = YOLO("yolov8n.pt")
        frame = self.__get_frame(event)

        if frame is None:
            return

        results = model.predict(source=frame, save=False, verbose=False)

        predicted_classes = [""]

        for res in results:
            for box in res.boxes:
                idx = int(box.cls.item())
                class_name = res.names[idx]
                predicted_classes.append(class_name)
        self.__save_pred(event, predicted_classes)

    def __save_pred(self, event: Event, predicted_classes: list["str"]):
        log.debug(f"before save preds: {predicted_classes}")
        cache_db = PredCacheDatabase()
        cache_db.save_pred(event, predicted_classes)

    def __get_frame(self, event: Event) -> npt.ArrayLike:
        _img_db = ImgS3Database()
        frame = _img_db.get_frame_by_frame_id(event.stream_source)
        return frame

    def __clear_cache_db(self, event: Event):
        log.debug(f"before processes db clean for event:{event.request_uuid}")
        cache_db = PredCacheDatabase()
        cache_db.clear_after_event(event)


inference_service = InferenceService()
