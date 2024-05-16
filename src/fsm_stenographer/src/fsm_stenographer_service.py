import threading

from broker.broker_service import Broker
from fsm_stenographer_models import Event
from db.db_service import db


class FSMStenographer():
    _TOPICS = ["api_fsm_st", "runner_fsm_st", "inference_fsm_st"]

    def __init__(self, topics=_TOPICS):
        self.msg_broker = Broker(topics)

    def read_and_process_event(self):
        event: Event = self.msg_broker.consume_event()

        if not event:
            return

        self._update_request_state_table_with_event(event)

    def _update_request_state_table_with_event(self, event: Event) -> None:
        event_th = threading.Thread(
            target=db.update_state_table_with_event,
            args=(event,),
            daemon=True
        )
        event_th.start()


fsm_stenographer_service = FSMStenographer()
