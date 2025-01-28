import hashlib

from flask import Blueprint, jsonify, request
from opentelemetry import trace

from src.cache import get_redis_conn
from src.metrics import ArcadeMetrics

routes = Blueprint("routes", __name__)


@routes.route("/alive", methods=["GET"])
def alive():
    return jsonify(success=True)


@routes.route("/get_game_scores/", methods=["GET"])
def get_game_scores():
    redis = get_redis_conn()

    scoreboard = []

    for key in redis.scan_iter(match="scores:*"):
        score_entry = redis.hgetall(key)
        scoreboard.append(score_entry)

    return jsonify(scoreboard)


@routes.route("/get_quiz_scores/", methods=["GET"])
def get_quiz_scores():
    redis = get_redis_conn()

    scoreboard = []

    for key in redis.scan_iter(match="quiz:*"):
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
        f"scores:{scoreboard_update["player_name"]}:"
        + f"{scoreboard_update["title"]}:"
        + f"{scoreboard_update["game_session_id"]}",
        scoreboard_update,
    )

    ArcadeMetrics.scoreboard_metric_processor(attr=scoreboard_update)

    return {}


def get_question_hash(question: str) -> str:
    sha256_hash = hashlib.sha256()
    sha256_hash.update(question.encode("utf-8"))

    return sha256_hash.hexdigest()


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
        f"quiz:{quiz_update["player_name"]}:"
        + f"{quiz_update["title"]}:"
        + f"{quiz_update["game_session_id"]}:"
        + f"{get_question_hash(question=quiz_update["question"])}",
        quiz_update,
    )

    return {}


@routes.route("/player_seen_questions/<string:module>", methods=["GET"])
def get_player_seen_questions(module: str):
    player_name = request.headers.get("Player-Name")
    if not player_name:
        raise Exception("No Player Name provided")

    redis = get_redis_conn()

    seen_questions = []

    for key in redis.scan_iter(match=f"quiz:{player_name}:{module}:*"):
        seen_questions.append(redis.hget(key, "question"))

    return jsonify(seen_questions)
