import os
from dotenv import load_dotenv, find_dotenv
from psycopg2.pool import ThreadedConnectionPool
import psycopg2

from fsm_stenographer_models import Event
from logger import log

_env_file = find_dotenv(f'./.{os.getenv("ENV", "dev")}.env')
load_dotenv(_env_file)


class Database():
    def __init__(self):
        self.host = self._get_host()
        self.port = self._get_port()
        self.__user = self._get_db_user()
        self.__password = self._get_db_password()
        self.database = self._get_db()
        self.conn_pool = None
        self.is_ready = self.__init_tables()
        if self.is_ready:
            self.__is_healthy(1)

    def __del__(self):
        if self.conn_pool:
            self.conn_pool.closeall()

    def _get_host(self):
        host = os.environ['POSTGRES_DB_HOST']
        return host

    def _get_port(self):
        port = os.environ['POSTGRES_DB_PORT']
        return port

    def _get_db_user(self):
        user = os.environ['POSTGRES_USER']
        return user

    def _get_db_password(self):
        password = os.environ['POSTGRES_PASSWORD']
        return password

    def _get_db(self):
        basic_db = os.environ['POSTGRES_DB']
        return basic_db

    def __init_tables(self):
        try:
            self.conn_pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                user=self.__user,
                password=self.__password,
                host=self.host,
                port=self.port,
                database=self.database
            )

            _conn = self.conn_pool.getconn()

            if _conn:
                _curr = _conn.cursor()
                _curr.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS request_state (
                    request_uuid   VARCHAR (100) PRIMARY KEY,
                    state          VARCHAR (100) NOT NULL,
                    event         VARCHAR (100) NOT NULL,
                    stream_source  VARCHAR (100) NOT NULL
                    );
                    """
                )
                _curr.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS events (
                    event_id       SERIAL PRIMARY KEY,
                    request_uuid   VARCHAR (100) NOT NULL,
                    state          VARCHAR (100) NOT NULL,
                    event         VARCHAR (100) NOT NULL,
                    stream_source  VARCHAR (100) NOT NULL
                    );
                    """
                )
                _conn.commit()
                self.conn_pool.putconn(_conn)
            else:
                return False
            return True

        except (Exception, psycopg2.DatabaseError) as ex:
            log.critical(
                f"Error while connecting to db while init action with exception: {ex}")
        finally:
            return False

    def __is_healthy(self, val: int):
        val = str(val)
        os.environ["HEALTHY"] = val

    def update_state_table_with_event(self, event: Event):
        try:
            _conn = self.conn_pool.getconn()

            if _conn:
                _curr = _conn.cursor()
                _curr.execute(
                    f"""
                    INSERT INTO request_state (request_uuid, state, event, stream_source)
                    VALUES ('{event.request_uuid}', '{event.state}', '{event.event}', '{event.stream_source}')
                    ON CONFLICT (request_uuid)
                    DO UPDATE 
                    SET
                    state = EXCLUDED.state,
                    event = EXCLUDED.event
                    ;
                    """
                )
                _curr.execute(
                    f"""
                    INSERT INTO events (event_id, request_uuid, state, event, stream_source)
                    VALUES (DEFAULT ,'{event.request_uuid}', '{event.state}', '{event.event}', '{event.stream_source}');
                    """
                )
                _conn.commit()
            self.conn_pool.putconn(_conn)

            log.critical(f"""update fsm state with event: {event.event}, 
            request_uuid: {event.request_uuid},
            state: {event.state},
            stream_source: {event.stream_source}
            """)

        except (Exception, psycopg2.DatabaseError) as ex:
            log.critical(
                f"Error while connecting to db while insert/update action with exception: {ex}")


db = Database()
