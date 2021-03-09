import logging
import sys

formatter = logging.Formatter('%(levelname) -10s %(asctime)s %(module)s:%(lineno)s %(funcName)s %(message)s')

def basic_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Make sure we at least log to stdout
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger
