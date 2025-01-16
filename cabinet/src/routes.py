import os
import uuid
from datetime import UTC, datetime
from urllib.parse import urlsplit

import requests
import sqlalchemy as sa
from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from opentelemetry import trace

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
        user = db.first_or_404(sa.select(User).where(User.username == current_user.username))
        current_user.last_seen = datetime.now(UTC)
        db.session.commit()
        print(user.username)
        session["username"] = user.username
        session["user_id"] = user.id
        session["first_name"] = user.first_name
        session["last_name"] = user.last_name
        session["email"] = user.email


@routes.route("/alive", methods=["GET"])
def alive():
    return jsonify(success=True)


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


@routes.route("/gamelist", methods=["GET", "POST"])
@login_required
def gamelist():
    gamelist = db.session.query(Games)

    for g in Games.gamejson:
        # print(db.session.query(sa.sql.exists().where(Games.title == g['title'])).scalar())
        exists = db.session.query(Games).filter_by(title=g["title"]).scalar() is not None
        if not exists:
            games = Games()
            games.title = g["title"]
            games.description = g["description"]
            games.gameurl = g["uri"]
            db.session.add(games)
            db.session.commit()

    if current_user.is_authenticated:
        print(gamelist)
        return render_template("gamelist.html", gamelist=True, gameData=gamelist)
    else:
        return redirect(url_for("routes.login"))


@routes.route("/playgame", methods=["GET", "POST"])
@login_required
def playgame():
    user = db.first_or_404(sa.select(User).where(User.username == current_user.username))
    if current_user.is_authenticated:
        title = request.form.get("title")
        description = request.form["description"]
        uri = request.form.get("uri")
        return render_template(
            "playgame.html",
            playgame=True,
            gamelist=True,
            data={"title": title, "description": description, "uri": uri},
            user=user,
            gamesession=uuid.uuid4(),
        )
    else:
        return redirect(url_for("routes.login"))


@routes.route("/addgame")
@login_required
def addgame():
    if current_user.is_authenticated:
        return render_template("addgame.html", addgame=True, login=True)
    else:
        return redirect(url_for("routes.login"))


@routes.route("/login", methods=["GET", "POST"])
def login():
    u = User.admin_json
    # print(db.session.query(sa.sql.exists().where(Games.title == g['title'])).scalar())
    print(u["username"], u["password"])

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
        return redirect(url_for("routes.gamelist", login=True))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("routes.login"))
        login_user(user, remember=form.remember_me.data)
        # STORE USER INFO IN SESSION

        print(user)

        next_page = url_for("routes.login")
        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("routes.gamelist")
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


@routes.route("/addgames", methods=["POST"])
@login_required
def add_games():
    form = GameAddForm()
    if form.validate_on_submit():
        g = Games(
            title=form.title.data, description=form.description.data, gameurl=form.gameurl.data
        )
        print(form.title.data)
        print(form.description.data)
        print(form.gameurl.data)
        db.session.add(g)
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect(url_for("routes.get_games"))

    return render_template("add_game.html", title="Splunk Arcade Games", form=form)


@routes.route("/games", methods=["GET", "POST"])
@login_required
def get_games():
    form = GameDeleteForm()
    games = db.session.query(Games)

    return render_template("games.html", title="Splunk Arcade Games", games=games, form=form)


@routes.route("/deletegame/<int:game_id>", methods=["POST"])
@login_required
def delete_game(game_id):
    db.session.query(Games).filter_by(id=game_id).delete()
    db.session.commit()

    flash("Your changes have been saved.")
    return redirect(url_for("routes.get_games"))


@routes.route("/v2/add_game_data/", methods=["GET", "POST"])
def add_message():
    content = request.get_json(force=True)

    current_span = trace.get_current_span()
    for k, v in content.items():
        current_span.set_attribute(k, v)

    requests.post(
        f"http://{os.environ.get("SCOREBOARD_HOST", "scoreboard")}/v2/scoreboard-update/",
        json=content,
    )
    return content


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
