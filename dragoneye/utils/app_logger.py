import logging.handlers
import os

INITIALIZED = False
if not INITIALIZED:
    logger = logging.getLogger('dragoneye')
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    INITIALIZED = True


def add_file_handler(logger_directory) -> bool:
    try:
        os.makedirs(logger_directory, exist_ok=True)
        logger_file = os.path.join(logger_directory, 'dragoneye.log')
        rotate_file = os.path.isfile(logger_file)
        file_handler = logging.handlers.RotatingFileHandler(logger_file, maxBytes=10000000, backupCount=10)
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))
        if rotate_file:  # keeping log file per execution
            file_handler.doRollover()
        logger.addHandler(file_handler)
        return True
    except Exception:
        return False
