import os
import tempfile

import pytest

from videobookmarks import create_app
from videobookmarks.datamodel.datamodel import TagList
from videobookmarks.db import get_datamodel
from videobookmarks.db import init_app_datamodel

DB_URL = os.getenv('DB_URL')
if DB_URL is None:
    raise ValueError(
        "Missing DB_URL environment variable, could not connect to Database"
    )

if "_test" not in DB_URL:
    raise ValueError(
        "Make sure you are using the test database, not the normal one"
    )



@pytest.fixture
def app():
    # create the app with common test config
    app = create_app({"TESTING": True, "DATABASE": DB_URL})

    # connect to the database using the DB_URL provided above.
    with app.app_context():
        init_app_datamodel(app)

    yield app
    with app.app_context():
        # this is the teardown
        dm = get_datamodel()
        dm._connection.execute(
            "TRUNCATE users CASCADE;"
            "TRUNCATE tag CASCADE;"
            "TRUNCATE tag_list CASCADE;"
            "TRUNCATE video CASCADE;"
        )
        dm._connection.commit()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


class AuthActions:
    def __init__(self, client):
        self._client = client

    def register(self, username="test", password="test"):
        return self._client.post(
            "/authenticate/register",
            data={"username": username, "password": password},
            follow_redirects = True
        )

    def login(self, username="test", password="test"):
        return self._client.post(
            "/authenticate/login",
            data={"username": username, "password": password},
        )

    def logout(self):
        return self._client.get("/auth/logout", follow_redirects=True)


class CreateTagList:
    def __init__(self, app, suffix=None):
        with app.app_context():
            datamodel = get_datamodel()
            suffix = suffix or ''
            self.username = "na" + suffix
            self.user_id = datamodel.add_user(self.username, "na")
            self.video_id = datamodel.create_video_id(
                "youtube link" + suffix,
                "fakethumbnailurl.com",
                "fake youtube title",
            )
            self.tag_list_name = 'tag list name' + suffix
            self.tag_list_desc = 'tag list description'
            self.tag_list_id = datamodel.create_tag_list(
                self.tag_list_name,
                self.tag_list_desc,
                self.user_id,
            )
            self.created = datamodel.get_tag_list(self.tag_list_id).created

    @property
    def expected_tag_list(self):
        return TagList(
            id=self.tag_list_id,
            name=self.tag_list_name,
            description=self.tag_list_desc,
            username=self.username,
            user_id=self.user_id,
            created=self.created,
        )

@pytest.fixture
def auth(client):
    return AuthActions(client)
