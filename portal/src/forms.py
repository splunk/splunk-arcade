import re

import sqlalchemy as sa
from flask_wtf import FlaskForm
from markupsafe import Markup
from wtforms import BooleanField, PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NoneOf, ValidationError

from . import db
from .models import User

RFC1123_PATTERN = re.compile(r"[a-z0-9]([-a-z0-9]*[a-z0-9])?(\\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*")


def rfc1123(_, field):
    match = RFC1123_PATTERN.match(field.data)
    if match.group() != field.data:
        raise ValidationError(
            "Username must be valid RFC1123 style, this means: \n"
            "\tconsist of lower case alphanumeric characters, '-' or '.', and\n"
            "\tmust start and end with an alphanumeric character"
        )


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class GameAddForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    description = StringField("Description", validators=[DataRequired()])
    gameurl = StringField("Game URL", validators=[DataRequired()])
    submit = SubmitField("Add Game")


class GameDeleteForm(FlaskForm):
    submit = SubmitField("Delete Game")


class RegistrationForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            NoneOf(
                values=[
                    "devplayer",
                ],
                message="this username is not allowed.",
            ),
            rfc1123,
            Length(min=4, max=64),
        ],
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField("Repeat Password", validators=[DataRequired(), EqualTo("password")])
    accept_tos = BooleanField(
        Markup(
            """<a 
                    href="https://www.splunk.com/en_us/legal/splunk-general-terms.html" 
                    class="text-purple-400 hover:text-purple-500">
                I accept Terms and Conditions
            </a>"""
        ),
        validators=[DataRequired()],
    )
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError("Please use a different email address.")


class ProfileForm(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    twitter = StringField("Twitter")
    github = StringField("Github")
    linkedin = StringField("LinkedIn")
    url = StringField("URL")
    company = StringField("Company")
    password = PasswordField("Password", validators=[DataRequired()])

    password2 = PasswordField("Repeat Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError("Please use a different username.")

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError("Please use a different email address.")


class EditProfileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    about_me = TextAreaField("About me", validators=[Length(min=0, max=140)])
    submit = SubmitField("Submit")
