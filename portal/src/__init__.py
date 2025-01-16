import os

from flask import Flask
from flask_session import Session
from redis import StrictRedis

from src.db import db, migrate
from src.login import login
from src.routes import routes


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    SECRET_KEY = os.environ.get("SECRET_KEY")


def create_app():
    app = Flask(__name__)

    app.secret_key = os.getenv("SECRET_KEY")

    app.config.from_object(Config)
    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_REDIS"] = StrictRedis(
        host=os.getenv("REDIS_HOST", "cache"),
        port=6379,
        db=0,
    )

    login.init_app(app)
    login.login_view = "routes.login"

    Session(app)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(routes)

    return app
