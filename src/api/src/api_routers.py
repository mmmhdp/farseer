import os

from fastapi import APIRouter
from dotenv import load_dotenv, find_dotenv
from fastapi import Depends
from typing_extensions import Annotated

from src.api_models import RequestState, ShallowUserRequest, UserRequest
from src.api_services import api_services
from src.logger import log

__ENV_FILE = find_dotenv(f'.{os.getenv("ENV", "dev")}.env')
load_dotenv(__ENV_FILE)


class FarseerAPI:
    def __init__(self):
        self.version = self._get_api_version()
        self.prefix: str = f"/farseer/api/v{self.version}"
        self.router: APIRouter = APIRouter(prefix=self.prefix)
        self.tags = ["VIDEO_STREAM_ANALITICS"]
        self.router.add_api_route(
            "/get/request", self._get_detection_results, methods=["GET"], tags=self.tags)
        self.router.add_api_route(
            "/post", self._change_request_state, methods=["POST"], tags=self.tags)

    def _get_api_version(self):
        api_version = os.environ['API_VERSION']
        return api_version

    def _get_detection_results(
            self,
            request: Annotated[ShallowUserRequest, Depends()]) -> RequestState:

        log.debug(
            f"try get detection res for request with uuid: {request.request_uuid}")

        results: RequestState = api_services.get_request_state_by_request_uuid(
            request=request)
        return results

    def _change_request_state(
        self,
        request: Annotated[UserRequest, Depends()]
    ) -> RequestState:
        """
            there are two types of events: "start" and "stop"

            for "start" - stream_source is required

            for "stop" - request_uuid is required
        """

        log.debug(
            f"""try change request state for request 
            with uuid: {request.request_uuid} 
            event: {request.event} 
            stream_source: {request.stream_source}""")

        state: RequestState = api_services.update_request_state(request)
        return state


farseer_api_router = FarseerAPI().router
