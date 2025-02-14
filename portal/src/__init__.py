import os

from flask import Flask
from flask_session import Session
from redis import StrictRedis
from sqlalchemy import text

from src.db import db, migrate
from src.login import login
from src.routes import routes


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]

    SESSION_TYPE = "redis"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_SERIALIZATION_FORMAT = "json"
    SESSION_REDIS = StrictRedis(
        host=os.getenv("REDIS_HOST", "cache"),
        port=6379,
        db=0,
    )


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    login.init_app(app)
    login.login_view = "routes.login"

    Session(app)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(routes)

    with app.app_context():
        try:
            db.session.execute(text("SELECT 1"))
            db.create_all()
        except Exception as exc:
            # violently quit :)
            print(f"db not ready... exception: {exc}")
            os._exit(1)

    return app
