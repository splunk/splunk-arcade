import os
import uuid

import requests
from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from opentelemetry import trace

from src.db import db
from src.models import Games

routes = Blueprint("routes", __name__)


PLAYER_NAME = os.getenv("PLAYER_NAME")
ARCADE_HOST = os.getenv("ARCADE_HOST")
SCOREBOARD_HOST = os.getenv("SCOREBOARD_HOST")
PLAYER_CONTENT_HOST = os.getenv("PLAYER_CONTENT_HOST")


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
        return redirect(url_for("routes.gamelist", login=True))
    else:
        return redirect(url_for("routes.login"))


@routes.route("/login")
def login():
    return redirect(f"http://{ARCADE_HOST}/login", code=302)


@routes.route("/logout")
def logout():
    return redirect(f"http://{ARCADE_HOST}/logout", code=302)


@routes.route("/gamelist", methods=["GET", "POST"])
@login_required
def gamelist():
    gamelist = db.session.query(Games)

    for g in Games.gamejson:
        exists = db.session.query(Games).filter_by(title=g["title"]).scalar() is not None
        if not exists:
            games = Games()
            games.title = g["title"]
            games.description = g["description"]
            games.gameurl = g["uri"]
            db.session.add(games)
            db.session.commit()

    if current_user.is_authenticated:
        return render_template("gamelist.html", gamelist=True, gameData=gamelist)
    else:
        return redirect(url_for("routes.login"))


@routes.route("/playgame", methods=["GET", "POST"])
@login_required
def playgame():
    if current_user.is_authenticated:
        title = request.form.get("title")
        description = request.form["description"]
        uri = request.form.get("uri")
        return render_template(
            "playgame.html",
            playgame=True,
            gamelist=True,
            data={"title": title, "description": description, "uri": uri},
            user_username=current_user.username,
            user_uuid=current_user.uuid,
            gamesession=uuid.uuid4(),
            arcade_endpoint=f"http://{ARCADE_HOST}/player/{PLAYER_NAME}/v2/update_score/",
            quizendpoint=f"http://{ARCADE_HOST}/player/{PLAYER_NAME}/question/imvaders",
        )
    else:
        return redirect(url_for("routes.login"))


@routes.route("/v2/update_score/", methods=["POST"])
def update_score():
    content = request.get_json(force=True)

    current_span = trace.get_current_span()
    for k, v in content.items():
        current_span.set_attribute(k, v)

    requests.post(
        f"http://{SCOREBOARD_HOST}/v2/update/",
        json=content,
    )

    return {}


@routes.route("/question/<string:module>", methods=["GET"])
def get_question(module: str):
    content = requests.get(f"http://{PLAYER_CONTENT_HOST}/quiz/question/{module}")

    return content.json()


@routes.route("/walkthrough/<string:module>/<string:stage>", methods=["GET"])
def get_walkthrough(module: str, stage: str):
    content = requests.get(f"http://{PLAYER_CONTENT_HOST}/walkthrough/{module}/{stage}")

    return content.json()
