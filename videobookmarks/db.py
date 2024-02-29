from flask import Flask
from flask import current_app

from videobookmarks.datamodel.datamodel import PostgresDataModel


def get_datamodel() -> PostgresDataModel:
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    from flask import g

    if "datamodel" not in g or type(g.datamodel) != PostgresDataModel:
        g.datamodel = PostgresDataModel(current_app.config["DB_URL"])
    return g.datamodel


def close_datamodel() -> None:
    """If this request connected to the database, close the
    connection.
    """
    from flask import g

    datamodel = g.pop("datamodel", None)

    if datamodel is not None:
        datamodel.close()


def init_app_datamodel(app: Flask) -> None:
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_datamodel)
