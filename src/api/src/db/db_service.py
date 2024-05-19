import json
import os
import redis
from dotenv import load_dotenv, find_dotenv

from src.api_models import RequestState, ShallowUserRequest
from src.logger import log

_env_file = find_dotenv(f'./.{os.getenv("ENV", "dev")}.env')
load_dotenv(_env_file)


class Database():
    def __init__(self):
        self.host = self._get_host()
        self.port = self._get_port()
        self.__password = self._get_db_password()
        self.db_partition = 0
        self.conn = redis.Redis(
            host=self.host,
            password=self.__password,
            port=self.port,
            db=self.db_partition)

    def _get_host(self):
        host = os.environ['REDIS_DB_HOST']
        return host

    def _get_port(self):
        port = os.environ['REDIS_DB_PORT']
        return port

    def _get_db_password(self):
        password = os.environ['REDIS_HOST_PASSWORD']
        return password

    def query_request_state_by_request_uuid(
            self,
            request: ShallowUserRequest) -> RequestState:
        log.debug(
            f"try to get results for request with uuid: {request.request_uuid}")

        request_uuid = request.request_uuid
        is_here = self.conn.keys(request_uuid)

        if is_here:
            log.debug(f"data is existed for request with uuid: {request_uuid}")
            raw_state = self.conn.get(request_uuid)
            _state = json.loads(raw_state)
        else:
            _state = {}

        try:
            state = RequestState(**_state)
        except Exception as ex:
            log.error(
                f"Invalid params for create request object with exception: {ex}")
            state = RequestState()

        return state


db = Database()
