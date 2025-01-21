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
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from opentelemetry import trace

from src.cluster import (
    ARCADE_HOST,
    player_deployment_create,
    player_deployment_ready,
)
from src.db import db
from src.forms import (
    EditProfileForm,
    GameAddForm,
    GameDeleteForm,
    LoginForm,
    ProfileForm,
    RegistrationForm,
)
from src.models import Games, User

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


@routes.route("/whichuser", methods=["GET"])
def whichuser():
    if current_user.is_authenticated:
        if player_deployment_ready(player_id=session["username"]):
            resp = make_response(
                redirect(f"http://{ARCADE_HOST}/player/{session["username"]}", code=302),
            )

            return resp

        return render_template("logged-in-waiting.html", title="Home", user=session)

    return redirect(url_for("routes.login"))


@routes.route("/")
@login_required
def index():
    return render_template("index.html", title="Home", user=session)


@routes.route("/profile", methods=["GET", "POST"])
@login_required
def profile_page():
    form = ProfileForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            uuid=uuid.uuid4(),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            twitter=form.twitter.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

    if current_user.is_authenticated:
        return render_template("profile.html", title="Home", user=session, form=form)
    else:
        return redirect(url_for("routes.login"))


@routes.route("/home")
@login_required
def home():
    if current_user.is_authenticated:
        return render_template("home.html", home=True, login=True)
    else:
        return redirect(url_for("routes.login"))


@routes.route("/login", methods=["GET", "POST"])
def login():
    u = User.admin_json

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
        return redirect(url_for("routes.whichuser", login=True))

    form = LoginForm()

    if form.validate_on_submit():
        if form.username.data == "devplayer":
            devplayer_user = db.session.scalar(sa.select(User).where(User.username == "devplayer"))

            if devplayer_user is not None:
                login_user(devplayer_user, remember=False)
                return redirect(url_for("routes.whichuser", login=True))

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
            return redirect(url_for("routes.whichuser", login=True))

        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))

        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")

            return redirect(url_for("routes.login"))

        login_user(user, remember=form.remember_me.data)

        next_page = url_for("routes.login")

        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("routes.whichuser", login=True)

        return redirect(next_page)

    return render_template("auth-login-2.html", title="Sign In", form=form)


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


@routes.route("/user/<username>")
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    posts = [{"author": user, "body": "Test post #1"}, {"author": user, "body": "Test post #2"}]
    return render_template("user.html", user=user, posts=posts)


@routes.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect(url_for("routes.edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", title="Edit Profile", form=form)


@routes.route("/otel-health", methods=["GET"])
def otel_health():
    otelhealth = requests.get(os.environ.get("OTEL_EXPORTER_HEALTH_ENDPOINT"))

    print(otelhealth.json())
    current_span = trace.get_current_span()
    for k, v in otelhealth.json().items():
        current_span.set_attribute(k, v)
    if otelhealth.json()["status"] == "Server available":
        data = {"message": "Hello from Flask!"}
        return jsonify(data)
    else:
        return "Opentelemetry Collector Offline"
