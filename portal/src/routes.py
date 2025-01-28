import os
import uuid
from datetime import UTC, datetime
from urllib.parse import urlsplit

import requests
import sqlalchemy as sa
from flask import (
    Blueprint,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from opentelemetry import trace

from src.cluster import (
    APP_NAME,
    ARCADE_HOST,
    player_deployment_create,
    player_deployment_ready,
)
from src.db import db
from src.forms import (
    LoginForm,
    RegistrationForm,
)
from src.models import User

routes = Blueprint("routes", __name__)


@routes.before_request
def before_request():
    if current_user.is_authenticated:
        found_user = db.first_or_404(sa.select(User).where(User.username == current_user.username))
        current_user.last_seen = datetime.now(UTC)
        db.session.commit()
        session["username"] = found_user.username
        session["user_id"] = found_user.id
        session["first_name"] = found_user.first_name
        session["last_name"] = found_user.last_name
        session["email"] = found_user.email


@routes.route("/alive", methods=["GET"])
def alive():
    return jsonify(success=True)


@routes.app_errorhandler(404)
def page_not_found_handler(e):
    _ = e

    # redirect anything that would 404 to index
    return redirect(url_for("routes.index"))


@routes.app_errorhandler(Exception)
def exception_handler(e):
    # crash for any non 404 exception, we want to let k8s deal w/ crash loop
    print(f"unhandled exception {e}, crashing... bye")
    os._exit(1)


@routes.route("/")
@login_required
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("routes.login"))

    return redirect(url_for("routes.wait_arcade", login=True))


@routes.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("routes.wait_arcade", login=True))

    form = LoginForm()

    if form.validate_on_submit():
        if form.username.data == "devplayer":
            devplayer_user = db.session.scalar(sa.select(User).where(User.username == "devplayer"))

            if devplayer_user is not None:
                login_user(devplayer_user, remember=False)
                return redirect(url_for("routes.wait_arcade", login=True))

            # ensure devplayer user exists
            devplayer_user = User(
                username="devplayer",
                email="devplayer@splunk.com",
                uuid=uuid.uuid4(),
                first_name="dev",
                last_name="player",
            )
            devplayer_user.set_password("password")
            db.session.add(devplayer_user)
            db.session.commit()

            login_user(devplayer_user, remember=False)
            return redirect(url_for("routes.wait_arcade", login=True))

        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))

        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")

            return redirect(url_for("routes.login"))

        login_user(user, remember=form.remember_me.data)

        next_page = url_for("routes.login")

        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("routes.wait_arcade", login=True)

        return redirect(next_page)

    return render_template("auth-login.html", title="Log In", form=form)


@routes.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("routes.login"))


@routes.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("routes.index"))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            uuid=uuid.uuid4(),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!")

        # create the players deployment
        player_deployment_create(form.username.data)

        return redirect(url_for("routes.login"))

    return render_template("auth-register.html", title="Register", form=form)


@routes.route("/wait-arcade", methods=["GET"])
def wait_arcade():
    if not current_user.is_authenticated:
        return redirect(url_for("routes.login"))

    if player_deployment_ready(player_id=session["username"]):
        resp = make_response(
            redirect(f"http://{ARCADE_HOST}/player/{session["username"]}", code=302),
        )

        return resp

    return render_template("wait-arcade.html", title="Waiting", user=session)


def calculate_quiz_answer_score(
    attempts: int,
    time_taken: float,
) -> float:
    attempt_score = {1: 1.0, 2: 0.75, 3: 0.5, 4: 0.25}.get(attempts, 0)

    time_score = max(0, min(1, 1 - (time_taken / 3600)))

    total_score = (attempt_score + time_score) / 2

    return round(total_score * 100)


def calculate_blended_score(
    game_score: int,
    quiz_score: int,
    max_game_score: int,
):
    game_weight = 0.6
    quiz_weight = 0.4

    normalized_game_score = game_score / max_game_score if max_game_score > 0 else 0

    overall_score = (normalized_game_score * game_weight) + (quiz_score * quiz_weight)

    return round(overall_score)


@routes.route("/scoreboard")
@login_required
def scoreboard():
    if not current_user.is_authenticated:
        return redirect(url_for("routes.login"))

    game_scores = requests.get(f"http://{APP_NAME}-scoreboard/get_game_scores")

    _high_scores_per_game_session = {}
    for game_score in game_scores.json():
        if game_score["game_session_id"] not in _high_scores_per_game_session:
            _high_scores_per_game_session[game_score["game_session_id"]] = {
                "title": game_score["title"],
                "version": game_score["version"],
                "player_name": game_score["player_name"],
                "current_score": int(game_score["current_score"]),
            }
            continue

        if (
            game_score["current_score"]
            > _high_scores_per_game_session[game_score["game_session_id"]]["current_score"]
        ):
            _high_scores_per_game_session[game_score["game_session_id"]]["current_score"] = int(
                game_score["current_score"]
            )

    _high_scores_cumulative = {}
    for game_score in game_scores.json():
        if game_score["player_name"] not in _high_scores_cumulative:
            _high_scores_cumulative[game_score["player_name"]] = {
                "title": game_score["title"],
                "player_name": game_score["player_name"],
                "current_score": int(game_score["current_score"]),
            }
            continue

        _high_scores_cumulative[game_score["player_name"]]["current_score"] += int(
            game_score["current_score"]
        )

    quiz_scores = requests.get(f"http://{APP_NAME}-scoreboard/get_quiz_scores")

    _high_scores_quiz = {}
    for quiz_score in quiz_scores.json():
        if quiz_score["player_name"] not in _high_scores_quiz:
            _high_scores_quiz[quiz_score["player_name"]] = {
                "player_name": quiz_score["player_name"],
                "current_score": calculate_quiz_answer_score(
                    attempts=int(quiz_score["attempts"]), time_taken=float(quiz_score["time_taken"])
                ),
            }
            continue

        _high_scores_quiz[quiz_score["player_name"]]["current_score"] += (
            calculate_quiz_answer_score(
                attempts=int(quiz_score["attempts"]), time_taken=float(quiz_score["time_taken"])
            )
        )

    _high_scores = _high_scores_quiz.values()
    max_game_score = 0

    if _high_scores:
        max_game_score = max(_high_scores_quiz.values(), key=lambda k: k["current_score"])[
            "current_score"
        ]

    _high_scores_blended = {}
    for player_name in _high_scores_cumulative.keys():
        _high_scores_blended[player_name] = {
            "player_name": player_name,
            "current_score": calculate_blended_score(
                game_score=_high_scores_cumulative[player_name]["current_score"],
                quiz_score=_high_scores_quiz.get(player_name, {}).get("current_score", 0),
                max_game_score=max_game_score,
            ),
        }

    return render_template(
        "scoreboard.html",
        title="Scoreboard",
        user=session,
        high_scores_per_game_session=sorted(
            [data for data in _high_scores_per_game_session.values()],
            key=lambda x: x["current_score"],
            reverse=True,
        )[:10],
        high_scores_cumulative=sorted(
            [data for data in _high_scores_cumulative.values()],
            key=lambda x: x["current_score"],
            reverse=True,
        )[:10],
        high_scores_quiz=sorted(
            [data for data in _high_scores_quiz.values()],
            key=lambda x: x["current_score"],
            reverse=True,
        )[:10],
        high_scores_blended=sorted(
            [data for data in _high_scores_blended.values()],
            key=lambda x: x["current_score"],
            reverse=True,
        )[:10],
    )


@routes.route("/otel-health", methods=["GET"])
def otel_health():
    otelhealth = requests.get(os.environ.get("OTEL_EXPORTER_HEALTH_ENDPOINT"))

    current_span = trace.get_current_span()

    for k, v in otelhealth.json().items():
        current_span.set_attribute(k, v)

    if otelhealth.json()["status"] == "Server available":
        data = {"message": "Hello from Flask!"}
        return jsonify(data)
    else:
        return "Opentelemetry Collector Offline"
