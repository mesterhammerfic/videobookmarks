from videobookmarks.db import get_datamodel
from flask import g, session


def test_register(app, client):
    response = client.post(
        '/authenticate/register', data={'username': 'a', 'password': 'a'}
    )
    assert response.headers["Location"] == "/authenticate/login"

    with app.app_context():
        user = get_datamodel()._connection.execute(
            "SELECT * FROM users WHERE username = 'a'",
        ).fetchone()
        assert user is not None


def test_login(app, client, auth):
    auth.register()
    auth.login()
    with client:
        client.get('/')
        assert g.user.username == 'test'


def test_logout(client, auth):
    auth.login()
    with client:
        auth.logout()
        assert 'user_id' not in session
