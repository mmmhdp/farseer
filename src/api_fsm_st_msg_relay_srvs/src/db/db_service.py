import os
import json

import redis
import psycopg2
from dotenv import load_dotenv, find_dotenv

from api_outbox_models import Event
from logger import log

_env_file = find_dotenv(f'./.{os.getenv("ENV", "dev")}.env')
load_dotenv(_env_file)


class PredDatabase():
    def __init__(self):
        self.host = self._get_host()
        self.port = self._get_port()
        self.__password = self._get_db_password()
        self.database = self._get_db()
        self.conn = redis.Redis(
            host=self.host,
            port=self.port,
            password=self.__password,
            db=self.database,
        )

    def __del__(self):
        self.conn.close()

    def _get_host(self):
        host = os.environ['PRED_REDIS_DB_HOST']
        return host

    def _get_port(self):
        port = os.environ['PRED_REDIS_DB_PORT']
        return port

    def _get_db_password(self):
        password = os.environ['PRED_REDIS_HOST_PASSWORD']
        return password

    def _get_db(self):
        db_partition = 0
        return db_partition

    def get_pred_for_event(self, event: Event) -> str:
        log.debug(f"get preds for event: {event.request_uuid}")

        _uuid = event.request_uuid
        if self.conn.keys(_uuid):
            pred = self.conn.get(_uuid)
        else:
            pred = ""

        log.debug(f"get preds: {pred} for event: {event.request_uuid}")
        return pred


class APIEventDatabase():
    def __init__(self):
        self.host = self._get_host()
        self.port = self._get_port()
        self.__password = self._get_db_password()
        self.database = self._get_db()
        self.conn = redis.Redis(
            host=self.host,
            port=self.port,
            password=self.__password,
            db=self.database,
        )

    def __del__(self):
        self.conn.close()

    def _get_host(self):
        host = os.environ['API_REDIS_DB_HOST']
        return host

    def _get_port(self):
        port = os.environ['API_REDIS_DB_PORT']
        return port

    def _get_db_password(self):
        password = os.environ['API_REDIS_HOST_PASSWORD']
        return password

    def _get_db(self):
        db_partition = 0
        return db_partition

    def save_update(self, pair: tuple[Event, str]):
        log.debug(
            f"update state for pair: event: {pair[0].request_uuid}, preds: {pair[1]}")

        event: Event = pair[0]
        preds = pair[1]

        if isinstance(preds, bytes):
            preds = preds.decode()

        request_state = {
            "request_uuid": "0",
            "init_startup": "0",
            "in_startup_processing": "0",
            "init_shutdown": "0",
            "in_shutdown_processing": "0",
            "active": "0",
            "inactive": "0",
            "detected_objects": preds.split()
        }
        request_state[event.state] = "1"
        raw_request_state = json.dumps(request_state)
        self.conn.set(event.request_uuid, raw_request_state)


class FsmStateDatabase():
    def __init__(self):
        self.host = self._get_host()
        self.port = self._get_port()
        self.__user = self._get_db_user()
        self.__password = self._get_db_password()
        self.database = self._get_db()
        self.conn = None
        self.last_updated_event_index = 0

        self.__init_tables()

    def __del__(self):
        if self.conn:
            self.conn.close()

    def _get_host(self):
        host = os.environ['FSM_POSTGRES_DB_HOST']
        return host

    def _get_port(self):
        port = os.environ['FSM_POSTGRES_DB_PORT']
        return port

    def _get_db_user(self):
        user = os.environ['FSM_POSTGRES_USER']
        return user

    def _get_db_password(self):
        password = os.environ['FSM_POSTGRES_PASSWORD']
        return password

    def _get_db(self):
        basic_db = os.environ['FSM_POSTGRES_DB']
        return basic_db

    def __init_tables(self):
        try:
            self.conn = psycopg2.connect(
                user=self.__user,
                password=self.__password,
                host=self.host,
                port=self.port,
                database=self.database
            )
        except (Exception, psycopg2.DatabaseError) as ex:
            log.critical(
                f"Error while connecting to db while init action with exception: {ex}")

    def get_current_events_updates(self) -> list[Event]:
        try:
            _conn = self.conn

            if _conn:
                _curr = _conn.cursor()
                rows = _curr.execute(
                    f"""
                    SELECT * FROM events WHERE event_id > {self.last_updated_event_index};
                    """
                )

                events = []
                rows = _curr.fetchall()

                if len(rows) > 0:
                    for row in rows:
                        event_id, request_uuid, state, event, stream_source = row
                        event = Event(
                            request_uuid=request_uuid,
                            state=state,
                            event=event,
                            stream_source=stream_source
                        )
                        events.append(event)

                    self.last_updated_event_index = int(rows[-1][0])

            return events

        except (Exception, psycopg2.DatabaseError) as ex:
            log.critical(
                f"Error while connecting to db while insert/update action with exception: {ex}")
            return []
        finally:
            _curr.close()


class OutboxService:
    def __init__(self):
        self.fsm_db = FsmStateDatabase()
        self.pred_db = PredDatabase()
        self.api_db = APIEventDatabase()

    def get_pred_event_pairs(self) -> list[tuple[Event, str]]:
        fsm_db = self.fsm_db
        events = fsm_db.get_current_events_updates()
        events_preds = []
        for event in events:
            pred = self._get_pred_by_request_uuid(event)
            pair = (event, pred)
            events_preds.append(pair)
        return events_preds

    def _get_pred_by_request_uuid(self, event: Event) -> str:
        pred_db = self.pred_db
        pred = pred_db.get_pred_for_event(event)
        return pred

    def update_state_with_preds(self):
        api_db = self.api_db
        pairs = self.get_pred_event_pairs()
        for pair in pairs:
            api_db.save_update(pair)


outbox_service = OutboxService()
