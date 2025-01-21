from flask import Blueprint, jsonify, request
from opentelemetry import trace

from src.cache import get_redis_conn
from src.metrics import ArcadeMetrics

routes = Blueprint("routes", __name__)


@routes.route("/alive", methods=["GET"])
def alive():
    return jsonify(success=True)


@routes.route("/v2/", methods=["GET"])
def get_scoreboard():
    redis = get_redis_conn()

    scoreboard = {}

    for key in redis.scan_iter():
        if redis.type(key) == "hash":
            hash_data = redis.hgetall(key)

            for field, value in hash_data.items():
                scoreboard[field] = value

    return jsonify(scoreboard)


@routes.route("/v2/update/", methods=["POST"])
def update_scoreboard():
    redis = get_redis_conn()

    content = request.get_json()
    current_span = trace.get_current_span()

    attr = {}

    for k, v in content.items():
        current_span.set_attribute(k, v)
        attr[k] = v

    scoreboard_update = {}

    for k, v in content.items():
        if isinstance(v, bool) or isinstance(v, list):
            x = str(v)
        else:
            x = v
        scoreboard_update[k] = x

    redis.hmset(scoreboard_update["game_session_id"], scoreboard_update)

    ArcadeMetrics.scoreboard_metric_processor(attr=scoreboard_update)

    return "Scoreboard updated successfully!"
