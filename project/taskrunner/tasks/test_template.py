import sys

import requests

from project.globals import logger


class TestTask(object):
    """Test task template"""
    def __init__(self):
        logger.info(f"{sys._getframe(0).f_code.co_name}")

    def run(self, **kwargs):
        """
        This is the only required method in a task - everything else is flexible
        Always return a value for `message` to be included in the response
        Include a status of 200 (success) or 500 (failure)
        """
        message = None
        status = 500     # default; return 200 on success
        cost = 0         # default; return cost based on query_job if applicable

        logger.info(f"{sys._getframe(0).f_code.co_name}")
        url = 'http://nvie.com'
        resp = requests.get(url)
        length = len(resp.text.split())
        if length > 0:
            message = f"The page at {url} has {length} words"
            status = 200

        return {'status': status, 'message': message, 'cost': cost}
