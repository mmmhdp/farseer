import os
from dotenv import load_dotenv, find_dotenv
from psycopg2.pool import ThreadedConnectionPool
import psycopg2

from src.fsm_stenographer_models import Event
from src.logger import log

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
            self.__up_health(1)

    def __del__(self):
        if self.conn_pool:
            self.conn_pool.closeall()

    def _get_host(self):
        try:
            host = os.environ['POSTGRES_DB_HOST']
        except KeyError:
            host = "localhost"
        return host

    def _get_port(self):
        try:
            port = os.environ['POSTGRES_DB_PORT']
        except KeyError:
            port = "5432"
        return port

    def _get_db_user(self):
        try:
            user = os.environ['POSTGRES_USER']
        except KeyError:
            user = "postgres"
        return user

    def _get_db_password(self):
        try:
            password = os.environ['POSTGRESS_PASSWORD']
        except KeyError:
            password = "password"
        return password

    def _get_db(self):
        try:
            basic_db = os.environ['POSTGRES_DB']
        except KeyError:
            basic_db = "postgres"
        return basic_db

    def __init_tables(self):
        try:
            self.conn_pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                username=self.__user,
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
                    CREATE TABLE request_state (
                    request_uuid   VARCHAR (100) PRIMARY KEY,
                    state          VARCHAR (100) NOT NULL,
                    event,         VARCHAR (100) NOT NULL,
                    stream_source  VARCHAR (100) NOT NULL,
                    );
                    """
                )
                _curr.execute(
                    f"""
                    CREATE TABLE events (
                    event_id       SERIAL PRIMARY KEY,
                    request_uuid   VARCHAR (100) UNIQUE NOT NULL,
                    state          VARCHAR (100) NOT NULL,
                    event,         VARCHAR (100) NOT NULL,
                    stream_source  VARCHAR (100) NOT NULL,
                    );
                    """
                )
                _conn.commit()
            else:
                return False
            self.conn_pool.putconn(_conn)
            return True
        except (Exception, psycopg2.DatabaseError) as ex:
            log.critical(
                f"Error while connecting to db while init action with exception: {ex}")
        finally:
            return False

    def __up_health(self, val: int):
        val = str(val)
        os.environ["HEALTHY"] = 1

    def update_state_table_with_event(self, event: Event):
        try:
            _conn = self.conn_pool.getconn()

            if _conn:
                _curr = _conn.cursor()
                _curr.execute(
                    f"""
                    INSERT INTO request_state (request_uuid, state, event, stream_source)
                    VALUES ({event.request_uuid}, {event.state}, {event.event}, {event.stream_source})
                    ON CONFLICT (request_uuid)
                    DO UPDATE SET
                    state = EXCLUDED.state
                    event = EXCLUDED.event;
                    """
                )
                _curr.execute(
                    f"""
                    INSERT INTO events (request_uuid, state, event, stream_source)
                    VALUES ({event.request_uuid}, {event.state}, {event.event}, {event.stream_source})
                    ON CONFLICT (request_uuid) DO NOTHING;
                    """
                )
                _conn.commit()
            self.conn_pool.putconn(_conn)
        except (Exception, psycopg2.DatabaseError) as ex:
            log.critical(
                f"Error while connecting to db while insert/update action with exception: {ex}")


db = Database()
