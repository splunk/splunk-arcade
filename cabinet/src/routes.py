import os
import uuid

import requests
from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from opentelemetry import trace

from src.db import db
from src.login import login
from src.models import User

routes = Blueprint("routes", __name__)


PLAYER_NAME = os.getenv("PLAYER_NAME")
ARCADE_HOST = os.getenv("ARCADE_HOST")
SCOREBOARD_HOST = os.getenv("SCOREBOARD_HOST")
PLAYER_CONTENT_HOST = os.getenv("PLAYER_CONTENT_HOST")


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


@routes.route("/alive", methods=["GET"])
def alive():
    return jsonify(success=True)


@routes.app_errorhandler(404)
def page_not_found(e):
    _ = e

    # redirect anything that would 404 to index
    return redirect(url_for("routes.index"))


@routes.route("/")
@login_required
def index():
    if current_user.is_authenticated:
        return redirect(url_for("routes.home", login=True))
    else:
        return redirect(url_for("routes.login"))


@routes.route("/login")
def login():
    return redirect(f"http://{ARCADE_HOST}/login", code=302)


@routes.route("/logout")
def logout():
    return redirect(f"http://{ARCADE_HOST}/logout", code=302)


@routes.route("/home", methods=["GET", "POST"])
@login_required
def home():
    if not current_user.is_authenticated:
        return redirect(url_for("routes.login"))

    return render_template(
        "home.html",
        scoreboard_endpoint=f"http://{ARCADE_HOST}/scoreboard",
        logout_endpoint=f"http://{ARCADE_HOST}/logout",
    )


@routes.route("/game", methods=["GET", "POST"])
@login_required
def game():
    if not current_user.is_authenticated:
        return redirect(url_for("routes.login"))

    return render_template(
        "game.html",
        playgame=True,
        gamelist=True,
        data={
            "title": request.form.get("title"),
            "description": request.form["description"],
            "uri": request.form.get("uri"),
        },
        user_username=current_user.username,
        user_uuid=current_user.uuid,
        gamesession=uuid.uuid4(),
        scoreboard_endpoint=f"http://{ARCADE_HOST}/scoreboard",
        logout_endpoint=f"http://{ARCADE_HOST}/logout",
    )


@routes.route("/record_game_score/", methods=["POST"])
def record_game_score():
    content = request.get_json(force=True)

    current_span = trace.get_current_span()
    for k, v in content.items():
        current_span.set_attribute(k, v)
    ###Check to see if they are playing the slow IMVADERS Version.  If SLOW Add a request attemo to a KNOWN Blackhole route on the scoreboard
    if content["title"] == "imvaders" and content["version"] == "0.75":
        try:
            ret = requests.post(f"http://{SCOREBOARD_HOST}/blackhole_sun/",json=content,)
        except:
            ret = requests.post(f"http://{SCOREBOARD_HOST}/record_game_score/",json=content,)
    else:
        ret = requests.post(
            f"http://{SCOREBOARD_HOST}/record_game_score/",
            json=content,
        )

    print(f"record game score status {ret.status_code}")

    return {}


@routes.route("/question/<string:module>", methods=["GET"])
def get_question(module: str):
    content = requests.get(
        f"http://{PLAYER_CONTENT_HOST}/quiz/question/{module}",
        headers={
            "Player-Name": PLAYER_NAME,
        },
    )

    return content.json()


@routes.route("/answer", methods=["POST"])
def record_answer():
    content = request.get_json(force=True)

    ret = requests.post(
        f"http://{SCOREBOARD_HOST}/record_quiz_score/",
        json=content,
    )

    print(f"record quiz score status {ret.status_code}")

    return {}

@routes.route("/reset_quiz_scores", methods=["POST"])
def reset_quiz_scores():
    ret = requests.post(
        f"http://{SCOREBOARD_HOST}/reset_player_quiz_scores",
        headers={
            "Player-Name": PLAYER_NAME,
        }
    )
    breakpoint()
    print(f"reset quiz score status {ret.status_code}")

    return {}

@routes.route("/walkthrough/<string:module>/<string:stage>", methods=["GET"])
def get_walkthrough(module: str, stage: str):
    content = requests.get(f"http://{PLAYER_CONTENT_HOST}/walkthrough/{module}/{stage}")

    if content.status_code == 422:
        # signal to the front end that they ran out of content
        return {}

    return content.json()
