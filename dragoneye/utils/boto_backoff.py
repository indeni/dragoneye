import functools
import time

from botocore.exceptions import ClientError

from dragoneye.utils.app_logger import logger

RATE_ERRORS = ['Throttling', 'TooManyRequestsException']


def rate_limiter(max_attempts=3):
    def decorator(func):
        @functools.wraps(func)
        def decorated(*args, **kwargs):
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except ClientError as ex:
                    if ex.response['Error']['Code'] not in RATE_ERRORS and ex.response['Error']['Message'] != 'Rate exceeded':
                        raise ex  # Raise non-throttling errors
                    attempt += 1
                    logger.warning(f'Throttling error on operation: {ex.operation_name} on attempt #{attempt}/{max_attempts}')
                    if attempt >= max_attempts:
                        raise ex
                    sleep_period = 2 ** (attempt + 2)
                    time.sleep(sleep_period)

        return decorated
    return decorator
