from dataclasses import dataclass


@dataclass
class Event:
    event: str
    state: str
    request_uuid: str
    stream_source: str
