import json
from src.broker.broker_producer_conf import producer_config
from confluent_kafka import Producer
from src.logger import log


class Broker:
    def __init__(self):
        self.producer = self._get_producer()

    def _get_producer(self):
        return Producer(**producer_config)

    def publish_event(self, request, topic, state):

        log.debug(f"try to publish event: {request.event} \
        with uuid: {request.request_uuid} \
        topic: {topic} \
        state: {state} \
        event: {request.event} \
        stream_source: {request.stream_source}\
         ")
        try:
            _topic = topic
            current_state = "init_startup"
            self.producer.produce(
                _topic,
                key=request.request_uuid,
                value=json.dumps(
                    {
                        "state": current_state,
                        "event": request.event,
                        "request_uuid": request.request_uuid,
                        "stream_source": request.stream_source,
                    }
                )
            )

            self.producer.flush()
            log.info(
                f"event: {request.event} \
                with request_uuid: {request.request_uuid} is published")

        except Exception as ex:
            log.error(
                f"failed to publish event: {request.event} \
                with request_uuid: {request.request_uuid} \
                because of exception: {ex}")


msg_broker = Broker()
