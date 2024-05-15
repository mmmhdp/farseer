from pydantic import BaseModel
from typing import Union


class UserRequest:
    def __init__(self, event: str, stream_source: Union[str, None], request_uuid: Union[str, None]):
        self.event = event
        self.stream_source = stream_source
        self.request_uuid = request_uuid


class ShallowUserRequest:
    def __init__(self, request_uuid: str):
        self.request_uuid = request_uuid


class RequestState(BaseModel):
    request_uuid: str = ""
    init_startup: str = "0"
    in_startup_processing: str = "0"
    init_shutdown: str = "0"
    in_shutdown_processing: str = "0"
    active: str = "0"
    inactive: str = "0"
    detected_objects: list[str] = [""]
