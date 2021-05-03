import os
import re


def validate_uuid(value: str, error_message='Invalid uuid format'):
    _validate_regex(value, r'^[0-9a-f]{8}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{4}\-[0-9a-f]{12}$', error_message)


def validate_path(value: str, error_message='Path does not exist'):
    if not os.path.exists(value):
        raise ValueError(error_message)


def _validate_regex(value: str,
                    regex: str,
                    error_message: str):

    result = re.match(regex, str(value))
    if not result:
        raise ValueError(error_message)
