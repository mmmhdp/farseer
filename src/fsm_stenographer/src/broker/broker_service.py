import json

from broker_producer_conf import producer_config
from broker_consumer_conf import consumer_config
from src.fsm_stenographer_models import Event
from src.logger import log

from confluent_kafka import Producer, Consumer, KafkaError, KafkaException


class Broker:
    def __init__(self, topics=[]):
        self.producer = self._get_producer()
        self.consumer = self._get_consumer()
        self.topics = topics

        self.consumer.subscribe(self.topics)

    def __del__(self):
        self.consumer.close()

    def _get_producer(self):
        return Producer(**producer_config)

    def _get_comsumer(self):
        return Consumer(**consumer_config)

    def consume_event(self):
        msg = self.consumer.poll(1.0)
        if msg is None:
            return None
        if msg.error():
            self.__process_broker_error(msg)
            return None

        message = self.__broker_msg_to_py_obj(msg)
        event = self.__assemble_event_from_message(message)
        return event

    def __assemble_event_from_message(self, message: dict[str:str]):
        event = Event(
            event=message["event"],
            state=message["state"],
            request_uuid=message["request_uuid"],
            stream_source=message["stream_source"]
        )
        return event

    def __broker_msg_to_py_obj(self, msg):
        msg = json.loads(msg.value().decode())
        return msg

    def __process_broker_error(self, msg) -> None:
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                log.error('%% %s [%d] reached end at offset %d\n' %
                          (msg.topic(), msg.partition(), msg.offset()))
            elif msg.error():
                try:
                    raise KafkaException(msg.error())
                except KafkaException(msg.error) as ex:
                    log.critical(f"kafka broker down with critical \
                    exception: {ex}")

    def publish_event(self, event: Event, topic: str, state: str) -> None:

        log.debug(f"try to publish event: {event.event} \
        with uuid: {event.request_uuid} \
        topic: {topic} \
        with previous state: {event.state} \
        and new state: {state} \
        event: {event.event} \
        stream_source: {event.stream_source}\
         ")
        try:
            _topic = topic
            current_state = state
            self.producer.produce(
                _topic,
                key=event.event_uuid,
                value=json.dumps(
                    {
                        "state": current_state,
                        "event": event.event,
                        "event_uuid": event.request_uuid,
                        "stream_source": event.stream_source,
                    }
                )
            )

            self.producer.flush()
            log.info(
                f"event: {event.event} \
                with event_uuid: {event.request_uuid} is published")

        except Exception as ex:
            log.error(
                f"failed to publish event: {event.event} \
                with event_uuid: {event.event_uuid} \
                because of exception: {ex}")


msg_broker = Broker()
