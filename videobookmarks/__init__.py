import os

from flask import Flask, request, redirect

from videobookmarks.datamodel.datamodel import PostgresDataModel

DB_URL = os.getenv('DB_URL')
if DB_URL is None:
    raise ValueError(
        "Missing DB_URL environment variable, could not connect to Database"
    )


def create_app(test_config=None):
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

    use_new_data_model = True
    # register the database commands
    from videobookmarks import db
    if not use_new_data_model:
        db.init_app(app)

        # apply the blueprints to the app
        from videobookmarks import auth, tag_list

        app.register_blueprint(auth.bp)
        app.register_blueprint(tag_list.bp)
    else:
        from videobookmarks import authenticate, tag
        db.init_app_datamodel(app)
        app.register_blueprint(authenticate.bp)
        app.register_blueprint(tag.bp)

    app.add_url_rule("/", endpoint="index")

    @app.before_request
    def before_request():
        if app.debug:
            return
        if request.is_secure:
            return

        url = request.url.replace("http://", "https://", 1)
        code = 301
        return redirect(url, code=code)

    return app
