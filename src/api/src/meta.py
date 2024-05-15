import os
from dotenv import load_dotenv, find_dotenv

__ENV_FILE = find_dotenv(f'.{os.getenv("ENV", "dev")}.env')
load_dotenv(__ENV_FILE)


def _get_api_title():
    try:
        api_title = os.environ['API_TITLE']
    except KeyError:
        api_title = "APP"
    return api_title


def _get_api_version():
    try:
        api_version = os.environ['API_VERSION']
    except KeyError:
        api_version = "0"
    return api_version


def _get_description():
    description = ""
    with open("README.md", "r") as readme:
        for line in readme.readlines():
            description += line
    return description


version = _get_api_version()
title = _get_api_title()
description = _get_description()
