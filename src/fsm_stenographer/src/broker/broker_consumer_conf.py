import os
from dotenv import load_dotenv, find_dotenv

__ENV_FILE = find_dotenv(f'.{os.getenv("ENV", "dev")}.env')
load_dotenv(__ENV_FILE)


class ConsumerConfig(object):
    def __init__(self):
        self.kafka_host = self._get_host()
        self.kafka_port = self._get_port()

    def _get_host(self):
        host = os.environ['KAFKA_BROKER_HOST']
        return host

    def _get_port(self):
        port = os.environ['KAFKA_BROKER_PORT']
        return port

    def get_config(self) -> dict[str:str]:
        config = {
            "bootstrap.servers": f"{self.kafka_host}:{self.kafka_port}",
            'group.id': 'fsm-stenographer',
            'auto.offset.reset': 'smallest'
        }
        return config


_config_manager = ConsumerConfig()
consumer_config = _config_manager.get_config()
