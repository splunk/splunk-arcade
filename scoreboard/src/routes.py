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

    scoreboard = []

    for key in redis.scan_iter(match="scores:*"):
        score_entry = redis.hgetall(key)
        scoreboard.append(score_entry)

    return jsonify(scoreboard)


@routes.route("/record_game_score/", methods=["POST"])
def record_game_score():
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

    redis.hmset(
        f"scores:{scoreboard_update["player_name"]}:{scoreboard_update["title"]}:{scoreboard_update["game_session_id"]}",
        scoreboard_update,
    )

    ArcadeMetrics.scoreboard_metric_processor(attr=scoreboard_update)

    return {}


@routes.route("/record_quiz_score/", methods=["POST"])
def record_quiz_score():
    redis = get_redis_conn()

    content = request.get_json()

    quiz_update = {}

    for k, v in content.items():
        if isinstance(v, bool) or isinstance(v, list):
            x = str(v)
        else:
            x = v
        quiz_update[k] = x

    redis.hmset(
        f"quiz:{quiz_update["player_name"]}:{quiz_update["title"]}:{quiz_update["game_session_id"]}",
        quiz_update,
    )

    return {}
