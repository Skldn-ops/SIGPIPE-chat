"""
Config class loads options from .env file
"""

import os
import sys
from dotenv import load_dotenv


# Load vars from .env
load_dotenv()


def must_get(key):
    """
    Get required envvar
    If var is not set, exits with error msg
    """
    res = os.getenv(key)
    if res is None:
        print(f"ERROR: envvar {key} is not set!")
        sys.exit(1)
    return res


def get(key, default_val):
    """
    Gets envvar
    If var is not set, sets it to default_val
    """
    res = os.getenv(key, default_val)
    return res


class Config:
    """
    Loads envvars from .env file
    ip and port are required
    """
    IP = must_get('ip')
    PORT = must_get('port')
