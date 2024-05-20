import logging
import os
from dotenv import load_dotenv, find_dotenv

_env_file = find_dotenv(f'.{os.getenv("ENV", "dev")}.env')
load_dotenv(_env_file)


class LoggerFactory:
    suffix = "_logger"
    basic_lvl = logging.INFO
    basic_format = "[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s"
    basic_datefmt = '%m-%d %H:%M:%S'
    basic_formatter = logging.Formatter(basic_format, basic_datefmt)

    @classmethod
    def get_logger(cls,
                   name="logger",
                   loglvl: str = logging.INFO,
                   to_stdout: bool = True):

        log_file_path = cls.__get_log_path(name)

        logging.basicConfig(
            filename=log_file_path,
            filemode='a',
            format=cls.basic_format,
            datefmt=cls.basic_datefmt,
            level=loglvl
        )

        name = name + cls.suffix
        new_logger_obj = logging.getLogger(name=name)

        if to_stdout:
            console = logging.StreamHandler()
            console.setLevel(loglvl)
            console.setFormatter(cls.basic_formatter)
            new_logger_obj.addHandler(console)
        return new_logger_obj

    @classmethod
    def __get_log_path(cls, name):
        path = os.environ["LOG_FILE_PATH"]
        return path


log = LoggerFactory.get_logger(
    name="infrerence_logger", loglvl=logging.INFO)
