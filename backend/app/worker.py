import os
import redis
from rq import Worker, Queue, Connection
from app.config import get_settings

settings = get_settings()
redis_url = settings.redis_url

listen = ['default']
redis_conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(redis_conn):
        worker = Worker(map(Queue, listen))
        worker.work()
