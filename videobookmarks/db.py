import os
import psycopg
from psycopg.rows import dict_row

import click
from flask import current_app
from flask import g

from videobookmarks.datamodel.datamodel import PostgresDataModel


def get_datamodel():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    if "datamodel" not in g:
        g.datamodel = PostgresDataModel(current_app.config["DB_URL"])
    return g.datamodel


def close_datamodel(e=None):
    """If this request connected to the database, close the
    connection.
    """
    datamodel = g.pop("datamodel", None)

    if datamodel is not None:
        datamodel.close()


def init_app_datamodel(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_datamodel)
