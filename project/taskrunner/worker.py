import os

import redis
from rq import Connection, Worker, Queue

def start_worker():
    redis_url = os.environ["REDIS_URL"]
    redis_connection = redis.from_url(redis_url)
    with Connection(redis_connection):
        worker = Worker(os.environ["QUEUES"])
        worker.work()

if __name__ == "__main__":
    start_worker()
