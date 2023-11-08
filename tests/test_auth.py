import os
import tempfile
import unittest
from videobookmarks import create_app
from videobookmarks.db import get_db
from .fixtures import AuthActions
from flask import g, session

DB_URL = os.getenv('DB_URL')
if DB_URL is None:
    raise ValueError(
        "Missing DB_URL environment variable, could not connect to Database"
    )
if "_test" not in DB_URL:
    raise ValueError(
        "Make sure you are using the test database, not the normal one"
    )

# read in SQL for populating test data
with open(os.path.join(os.path.dirname(__file__), "data.sql"), "rb") as f:
    _data_sql = f.read().decode("utf8")


class TestMyAPI(unittest.TestCase):
    def setUp(self):
        # create the app with common test config
        # Create a test client
        self.app = create_app({"TESTING": True, "DATABASE": DB_URL})
        self.client = self.app.test_client()
        self.runner = self.app.test_cli_runner()
        self.auth = AuthActions(self.client)
        with self.app.app_context():
            db = get_db()
            db.execute(
                """
                    CREATE TABLE users (
                        id SERIAL PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                    );

                    CREATE TABLE tag_list (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users ON DELETE CASCADE,
                        created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        name TEXT NOT NULL,
                        description TEXT
                    );

                    CREATE TABLE video (
                        id SERIAL PRIMARY KEY,
                        link TEXT NOT NULL
                    );

                    CREATE TABLE tag (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users ON DELETE CASCADE,
                        tag_list_id INTEGER REFERENCES tag_list ON DELETE CASCADE,
                        video_id INTEGER REFERENCES video ON DELETE CASCADE,
                        tag TEXT NOT NULL,
                        youtube_timestamp FLOAT NOT NULL,
                        created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                """
            )
            db.execute(_data_sql)
            db.commit()

    def tearDown(self):
        with (self.app.app_context()):
            db = get_db()
            db.execute(
                """ 
                    DROP TABLE tag;
                    DROP TABLE video;
                    DROP TABLE tag_list;
                    DROP TABLE users;
                """
            )
            db.commit()

    def test_register(self):
        response = self.client.post(
            '/auth/register', data={'username': 'a', 'password': 'a'}
        )
        self.assertEqual(response.headers["Location"],"/auth/login")

        with self.app.app_context():
            user = get_db().execute(
                "SELECT * FROM users WHERE username = 'a'",
            ).fetchone() is not None
            self.assertIsNotNone(user)

    def test_login(self):
        response = self.auth.login()
        self.assertEqual(response.headers["Location"], "/")

        with self.client:
            self.client.get('/')
            self.assertEqual(session['user_id'], 1)
            self.assertEqual(g.user['username'], 'test')

    def test_logout(self):
        self.auth.login()

        with self.client:
            self.auth.logout()
            self.assertNotIn('user_id', session)
