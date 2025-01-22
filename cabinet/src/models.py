from datetime import UTC, datetime
from hashlib import md5

import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import check_password_hash, generate_password_hash

from src.db import db
from src.login import login

Base = declarative_base()


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    first_name: so.Mapped[str | None] = so.mapped_column(sa.String(140))
    last_name: so.Mapped[str | None] = so.mapped_column(sa.String(140))

    password_hash: so.Mapped[str | None] = so.mapped_column(sa.String(256))
    uuid: so.Mapped[str | None] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[str | None] = so.mapped_column(sa.String(140))
    linkedin: so.Mapped[str | None] = so.mapped_column(sa.String(140))
    github: so.Mapped[str | None] = so.mapped_column(sa.String(140))
    twitter: so.Mapped[str | None] = so.mapped_column(sa.String(140))
    url: so.Mapped[str | None] = so.mapped_column(sa.String(140))
    company: so.Mapped[str | None] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[datetime | None] = so.mapped_column(default=lambda: datetime.now(UTC))

    posts: so.WriteOnlyMapped["Post"] = so.relationship(back_populates="author")

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}"


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(UTC))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)

    author: so.Mapped[User] = so.relationship(back_populates="posts")

    def __repr__(self):
        return f"<Post {self.body}>"


class Games(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(140))
    description: so.Mapped[str] = so.mapped_column(sa.String(140))
    gameurl: so.Mapped[str] = so.mapped_column(sa.String(140), nullable=True)
    gamejson = (
        {"title": "Logger", "description": "Hop to the log safely", "uri": "loggergame.html"},
        {
            "title": "imvader",
            "description": "Destroy UFOs while being shot at",
            "uri": "imvader.html",
        },
    )
