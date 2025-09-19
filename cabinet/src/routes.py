import logging
import os
import random
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
SPLUNK_OBSERVABILITY_REALM = os.getenv("SPLUNK_OBSERVABILITY_REALM", "us1")
ARCADE_O11Y_DASHBOARD = {"us1":"GvlHgXyAwBA?groupId=GvlBWCNA4A0&startTime=-1h&endTime=Now", "eu0":"Gv5GIONAEBg?groupId=Gv5GIONAEAQ&startTime=-1h&endTime=Now"}


IMVADERS_SLOW_VERSION = "0.75"
UNPROCESSABLE_ENTITY = 422


def _realmify_dashboard_url(url: str) -> str:
    return url.replace("app.signalfx.com", f"app.{SPLUNK_OBSERVABILITY_REALM}.signalfx.com")


FINAL_DASHBOARD_BASE_URL = _realmify_dashboard_url(
    os.getenv("dashboard_url", "https://app.signalfx.com/#/dashboard/"),
)

dashboard_path_for_realm = ARCADE_O11Y_DASHBOARD.get(SPLUNK_OBSERVABILITY_REALM, "us1")

FINAL_DASHBOARD_URL = f"{FINAL_DASHBOARD_BASE_URL}{dashboard_path_for_realm}"


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(f"player_cabinet_{PLAYER_NAME}")


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
        dashboard_home_endpoint=FINAL_DASHBOARD_URL,
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
        dashboard_home_endpoint=FINAL_DASHBOARD_URL,
    )


@routes.route("/questions", methods=["GET", "POST"])
@login_required
def questions():
    if not current_user.is_authenticated:
        return redirect(url_for("routes.login"))

    module = request.args.get('module')
    question_count = request.args.get('question_count')

    content = requests.get(
        f"http://{PLAYER_CONTENT_HOST}/quiz/questions/{module}/{question_count}",
        headers={
            "Player-Name": PLAYER_NAME,
        },
    )

    return render_template(
        "questions.html",
        user_username=current_user.username,
        module=module,
        scoreboard_endpoint=f"http://{ARCADE_HOST}/scoreboard",
        logout_endpoint=f"http://{ARCADE_HOST}/logout",
        dashboard_home_endpoint=FINAL_DASHBOARD_URL,
        question_content=content.json(),
    )


@routes.route("/record_game_score/", methods=["POST"])
def record_game_score():
    content = request.get_json(force=True)

    current_span = trace.get_current_span()
    for k, v in content.items():
        current_span.set_attribute(k, v)

    # if imvaders is on "slow" version (<1), trigger some failed http reqs
    if content["title"] == "imvaders" and content["version"] == IMVADERS_SLOW_VERSION:
        try:
            ret = requests.post(
                f"http://{SCOREBOARD_HOST}/blackhole_sun",
                json=content,
            )
            print(ret.status_code, ret.text)
        except Exception as exc:
            _ = exc
            pass

        # we dont record score for slow version! gotta answer questions to get your score
        # recorded!!
        return {}

    ret = requests.post(
        f"http://{SCOREBOARD_HOST}/record_game_score/",
        json=content,
    )

    print(f"record game score status {ret.status_code}")

    return {}


@routes.route("/answer", methods=["POST"])
def record_answer():
    content = request.get_json(force=True)

    ret = requests.post(
        f"http://{SCOREBOARD_HOST}/record_quiz_score/",
        json=content,
    )

    print(f"record quiz score status {ret.status_code}, text: {ret.text}")

    return {}


@routes.route("/record_question_thumbs_up_down", methods=["POST"])
def record_question_thumbs_up_down():
    # we'll have the js just send {"question": "the question prompt as this is unique enough to id"}
    content = request.get_json(force=True)

    ret = requests.post(
        f"http://{SCOREBOARD_HOST}/record_question_thumbs_up_down",
        headers={
            "Player-Name": PLAYER_NAME,
        },
        json=content,
    )

    print(f"record question thumps up/down status {ret.status_code}")

    return {}


@routes.route("/reset_quiz_scores", methods=["POST"])
def reset_quiz_scores():
    ret = requests.post(
        f"http://{SCOREBOARD_HOST}/reset_player_quiz_scores",
        headers={
            "Player-Name": PLAYER_NAME,
        },
    )

    print(f"reset quiz score status {ret.status_code}")

    return {}


@routes.route("/walkthrough/<string:module>/<string:stage>", methods=["GET"])
def get_walkthrough(module: str, stage: str):
    content = requests.get(f"http://{PLAYER_CONTENT_HOST}/walkthrough/{module}/{stage}")

    if content.status_code == UNPROCESSABLE_ENTITY:
        # signal to the front end that they ran out of content
        return {}

    return content.json()


@routes.route("/progression", methods=["GET"])
def get_progression():
    ret = requests.get(
        f"http://{SCOREBOARD_HOST}/player_progression",
        headers={
            "Player-Name": PLAYER_NAME,
        },
    )

    return ret.json()


@routes.route("/imvaders_version", methods=["GET"])
def get_imvaders_version():
    ret = requests.get(
        f"http://{SCOREBOARD_HOST}/player_progression",
        headers={
            "Player-Name": PLAYER_NAME,
        },
    )

    return {"version": ret.json()["game_versions"].get("imvaders") or 0.75}


@routes.route("/get_logger_version", methods=["GET"])
def get_logger_version():
    ret = requests.get(
        f"http://{SCOREBOARD_HOST}/player_progression",
        headers={
            "Player-Name": PLAYER_NAME,
        },
    )

    return {"version": ret.json()["game_versions"].get("logger") or 1.0}


@routes.route("/get_logger_ad/<string:version>/<int:life>", methods=["GET"])
def get_logger_ad(version: str, life: int):
    ads = [
        "Eat chicken, not frogs.",
        "Cross responsibly. Look both ways and then leap.",
        "Turtle taxis now 30% less snappy!",
        "Rain or shine, we jump on time.",
        "Today's special: Splat-free travel.",
        "Insert coin to not die.",
        "Lily pads cleaned daily. Probably.",
        "Hoppers wear Croaks™ — the #1 frog shoe.",
        "Avoid snakes. It’s not that deep.",
        "Friends don’t let frogs play in traffic."
    ]
    headers = {"Content-Type": "application/json"}
    payload = {"title": "ad request", "key": "no401"}


    if life == 666:
        try:
            ret = requests.post(
                f"http://{SCOREBOARD_HOST}/audit", json={"movement":"Moving LEFT failed"}, headers=headers
            )
            print("/audit: ", ret.status_code, ret.text)
        except Exception as exc:
            _ = exc
            pass
        return {"message": "[FAIL] Moving LEFT failed. Sending stored movements to /audit"}
    
    try:
        ret = requests.post(
            f"http://{SCOREBOARD_HOST}/kerplunkAds?version={version}", json=payload, headers=headers
        )
        print(ret.status_code, ret.text)
    except Exception as exc:
        _ = exc
        pass

    if life != 5 or version == "1.5":
        return {"message": "[ERROR] Ad failure ZGFlZCBzaSBncm9mLiBkYWVkIGlzIGx1YXAuIA=="}
    else:
        return {"message": random.choice(ads)}


    return {}


@routes.route("/are_you_not_entertained", methods=["GET", "POST"])
def are_you_not_entertained():
    return render_template("doom.html")


@routes.route("/log", methods=["POST"])
def log():
    content = request.get_json(force=True)

    current_span = trace.get_current_span()
    for k, v in content.items():
        current_span.set_attribute(k, v)

    logf = LOGGER.info

    title = content.get("title", "unknown title")
    message = content.get("message", "unknown message")

    logf(f'title: "{title}" | message: "{message}"')

    return {}
