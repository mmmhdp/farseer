import uuid

from fastapi import Depends
from typing_extensions import Annotated

from src.api_models import (
    ShallowUserRequest, UserRequest, RequestState
)
from src.db.db_service import db
from src.broker.broker_service import msg_broker
from src.logger import log

REQUEST_UUID_FOR_INVALID_SOURCE_FOR_START_EVENT = "-1"


class APIServices:
    def get_request_state_by_request_uuid(
            self,
            request: Annotated[ShallowUserRequest, Depends()]) -> RequestState:

        log.debug(f"inside get service api with uuid: {request.request_uuid}")

        state = db.query_request_state_by_request_uuid(request=request)
        return state

    def update_request_state(
        self, request: Annotated[UserRequest, Depends()]
    ) -> RequestState:

        if request.event == "start" and not request.stream_source:
            return RequestState(request_uuid=REQUEST_UUID_FOR_INVALID_SOURCE_FOR_START_EVENT)

        if not request.request_uuid:
            request.request_uuid = str(uuid.uuid4())

        log.debug(
            f"inside change state service api with uuid: {request.request_uuid}")

        topic_for_update_state_table = "api_fsm_st"
        topic_for_processing = "api_runner"
        state = "init_startup"

        msg_broker.publish_event(
            request=request,
            topic=topic_for_update_state_table,
            state=state)
        msg_broker.publish_event(
            request=request,
            topic=topic_for_processing,
            state=state)

        update_state_obj = RequestState(request_uuid=request.request_uuid)
        return update_state_obj


api_services = APIServices()
