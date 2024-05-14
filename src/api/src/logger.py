import logging
import os
from dotenv import load_dotenv, find_dotenv

_env_file = find_dotenv(f'.{os.getenv("ENV", "dev")}.env')
load_dotenv(_env_file)


class LoggerFactory:
    suffix = "_logger"
    basic_lvl = logging.INFO
    basic_formatter = logging.Formatter(
        '%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s')

    @classmethod
    def get_logger(cls,
                   name="logger",
                   loglvl: str = logging.INFO,
                   to_stdout: bool = True):

        log_file_path = cls.__get_log_path(name)

        logging.basicConfig(
            filename=log_file_path,
            filemode='a',
            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
            datefmt='%H:%M:%S',
            level=loglvl
        )

        name = name + cls.suffix
        new_logger_obj = logging.getLogger(name=name)

        if to_stdout:
            console = logging.StreamHandler()
            console.setLevel(cls.basic_lvl)
            console.setFormatter(cls.basic_formatter)
            new_logger_obj.addHandler(console)
        return new_logger_obj

    @classmethod
    def __get_log_path(cls, name):
        try:
            path = os.environ["LOG_FILE_PATH"]
        except KeyError:
            path = f".{name}_log.txt"
        return path


log = LoggerFactory.get_logger(name="api_logger")

log.info("big")
log.warning("zalupa")
