import os
import tempfile
import unittest
from videobookmarks import create_app
from videobookmarks.db import init_db, get_db
from .fixtures import AuthActions
from flask import g, session

# read in SQL for populating test data
with open(os.path.join(os.path.dirname(__file__), "data.sql"), "rb") as f:
    _data_sql = f.read().decode("utf8")


class TestMyAPI(unittest.TestCase):
    def setUp(self):
        # create a temporary file to isolate the database for each test
        db_fd, db_path = tempfile.mkstemp()
        self.db_fd = db_fd
        self.db_path = db_path
        # create the app with common test config
        # Create a test client
        self.app = create_app({"TESTING": True, "DATABASE": db_path})
        with self.app.app_context():
            init_db()
            get_db().executescript(_data_sql)
        self.client = self.app.test_client()
        self.runner = self.app.test_cli_runner()
        self.auth = AuthActions(self.client)

    def tearDown(self):
        # close and remove the temporary database
        os.close(self.db_fd)
        os.unlink(self.db_path)

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
