import os
from dotenv import load_dotenv, find_dotenv

__ENV_FILE = find_dotenv(f'.{os.getenv("ENV", "dev")}.env')
load_dotenv(__ENV_FILE)


class ProducerConfig(dict):
    def __init__(self):
        self.host = self._get_broker_host()
        self.port = self._get_broker_port()

    def _get_broker_host(self):
        host = os.environ['KAFKA_BROKER_HOST']
        return host

    def _get_broker_port(self):
        port = os.environ['KAFKA_BROKER_PORT']
        return port

    def get_config(self) -> dict[str:str]:
        config = {
            "bootstrap.servers": f"{self.host}:{self.port}"
        }
        return config


_config_manager = ProducerConfig()
producer_config = _config_manager.get_config()
