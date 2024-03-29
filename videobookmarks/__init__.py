import os
from typing import Optional, Mapping, Any

from flask import Flask, request, redirect, Response

DB_URL = os.getenv("DB_URL")
if DB_URL is None:
    raise ValueError(
        "Missing DB_URL environment variable, could not connect to Database"
    )


def create_app(test_config: Optional[Mapping[str, Any]] = None) -> Flask:
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DB_URL=DB_URL,
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # register the database commands
    from videobookmarks import db
    from videobookmarks import authenticate, tag

    db.init_app_datamodel(app)
    app.register_blueprint(authenticate.bp)
    app.register_blueprint(tag.bp)

    app.add_url_rule("/", endpoint="index")

    @app.before_request  # type: ignore
    def before_request() -> Optional[Response]:
        if app.debug:
            return None
        if test_config:
            return None
        if request.is_secure:
            return None

        url = request.url.replace("http://", "https://", 1)
        code = 301
        return redirect(url, code=code)

    return app
