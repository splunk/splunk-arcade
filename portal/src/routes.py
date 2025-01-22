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
    u = {"username": "admin", "email": "admin@splunk.com", "password": "password"}

    exists = db.session.query(User).filter_by(username=u["username"]).scalar() is not None
    if not exists:
        users = User()
        users.username = u["username"]
        users.email = u["email"]
        users.uuid = uuid.uuid4()
        users.set_password(u["password"])
        db.session.add(users)
        db.session.commit()

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


@routes.route("/scoreboard")
@login_required
def scoreboard():
    if not current_user.is_authenticated:
        return redirect(url_for("routes.login"))

    scores = requests.get(f"http://{APP_NAME}-scoreboard/v2/")

    return render_template(
        "scoreboard.html",
        title="Scoreboard",
        user=session,
        score_data=scores.json(),
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
