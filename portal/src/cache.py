import os

from flask import g
from redis import StrictRedis


def get_redis_conn():
    if "redis" not in g:
        g.redis = StrictRedis(
            host=os.getenv("REDIS_HOST", "cache"),
            port=6379,
            db=0,
            decode_responses=True,
        )

    return g.redis
