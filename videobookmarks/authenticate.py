import functools
from typing import Any, Union

import psycopg
from flask import Blueprint, Response
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.security import check_password_hash

from videobookmarks.db import get_datamodel

bp = Blueprint("authenticate", __name__, url_prefix="/authenticate")


def login_required(view):  # type: ignore
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs: str) -> Any:
        if g.user is None:
            return redirect(url_for("authenticate.login"))
        return view(**kwargs)

    return wrapped_view


@bp.before_app_request  # type: ignore
def load_logged_in_user() -> None:
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        datamodel = get_datamodel()
        g.user = datamodel.get_user_with_id(user_id)


@bp.route("/register", methods=("GET", "POST"))  # type: ignore
def register() -> Union[str, Response]:
    """
    Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        datamodel = get_datamodel()
        error = None
        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."

        if error is None:
            try:
                datamodel.add_user(username, password)
            except psycopg.IntegrityError:
                # The username was already taken, which caused the
                # commit to fail. Show a validation error.
                error = f"User {username} is already registered."
            else:
                # Success, go to the login page.
                return redirect(url_for("authenticate.login"))
        flash(error)
    return render_template("authenticate/register.html")


@bp.route("/login", methods=("GET", "POST"))  # type: ignore
def login() -> Union[str, Response]:
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None
        datamodel = get_datamodel()
        user = datamodel.get_user_with_name(username)
        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user.password, password):
            error = "Incorrect password."
        if error is None:
            # store the user id in a new session and return to the index
            destination = session.get(
                "login_referrer",
                url_for("authenticate.login"),
            )
            session.clear()
            session["user_id"] = user.id  # type: ignore
            return redirect(destination)
        flash(error)
    elif request.method == "GET":
        session["login_referrer"] = request.referrer
        print(session["login_referrer"])
    return render_template("authenticate/login.html")


@bp.route("/logout")  # type: ignore
def logout() -> Response:
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(request.referrer)
