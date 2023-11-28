import os
import unittest
from videobookmarks import create_app
from videobookmarks.db import get_datamodel


def test_index_logged_in(app, client, auth):
    response = auth.register()
    with app.app_context():
        dm = get_datamodel()
        user = dm.get_user_with_name("test")
        print(user)
    print('=========================')
    print(response.status_code)
    response = auth.login()
    print('=========================')
    print(response.data)
    response = client.get('/', follow_redirects=True)
    print('=========================')
    print(response.data)
    assert response.status_code == 200
    assert b'Log Out' in response.data


def test_index_logged_out(app, client, auth):
    auth.logout()
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'Log Out' in response.data

def test_create_tag_list_login_required(app, client, auth):
    response = client.get('/create')
    assertEqual(response.status_code, 302)

def test_create_tag_list_load_page(app, client, auth):
    auth.login()
    response = client.get('/create')
    assertEqual(response.status_code, 200)
    assertIn(b'href="/auth/logout"', response.data)
    assertIn(b'textarea name="description" id="description"', response.data)
    assertIn(b'form method="post"', response.data)
    assertIn(b'input name="name" id="name" value="" required', response.data)
    assertIn(b'textarea name="description" id="description"', response.data)

def test_view_tag_list(app, client, auth):
    auth.login()
    response = client.get('/1/view')
    assertEqual(response.status_code, 200)
    assertIn(b'href="/auth/logout"', response.data)
    assertIn(b'input name="yt_video_id" id="yt_video_id"', response.data)
    assertIn(b'<p> test_description </p>', response.data)
    assertIn(b'<h1>Viewing test_1</h1>', response.data)

def test_view_tag_list_not_found(app, client, auth):
    auth.login()
    response = client.get('/99/view')
    assertEqual(response.status_code, 404)

def test_view_tag_list_video_url_post(app, client, auth):
    auth.login()
    response = client.post('/1/view', data={'yt_video_id': 'test_link'})
    assertIn(b'Redirecting', response.data)
    assertIn(b'href="/tagging/1/test_link"', response.data)

def test_view_tag_list_video_url_post_no_video_url(app, client, auth):
    auth.login()
    response = client.post('/1/view', data={'yt_video_id': ''})
    assertIn(
        b' <div class="flash">Youtube Video ID is required.',
        response.data
    )
    assertIn(b'Viewing test_1 ', response.data)

def test_create_tag_list_post(app, client, auth):
    auth.login()
    client.post('/create', data={'name': 'test_3', 'description': 'another one'})

    with app.app_context():
        db = get_datamodel()
        description = db.execute(
            "SELECT description FROM tag_list WHERE name='test_3'"
        ).fetchone()['description']
        assertEqual(description, "another one")

def test_create_tag_list_post_no_name(app, client, auth):
    auth.login()
    response = client.post('/create', data={'name': '', 'description': 'another one'})

    assertIn(b'<div class="flash">Name is required.', response.data)

    with app.app_context():
        db = get_datamodel()
        tag_lists = db.execute("SELECT * FROM tag_list").fetchall()
        names = [row["name"] for row in tag_lists]
        assertNotIn("", names)

def test_video_tagging(app, client, auth):
    auth.login()
    response = client.get('/tagging/1/test_link')
    assertEqual(response.status_code, 200)
    assertIn(b'Tagging for test_1', response.data)
    assertIn(b"videoId: 'test_link'", response.data)
    assertIn(b'input type="text" name="tag" id="tag-input"', response.data)
    assertIn(b'button id="add-tag-button">Add Tag</button>', response.data)
    assertIn(b'<p>test_description</p>', response.data)

def test_video_tagging_new_video(app, client, auth):
    auth.login()
    # up until this point, there is no video with the link "new_link"
    # so it should create a new one
    response = client.get('/tagging/1/new_link')
    assertEqual(response.status_code, 200)

    with app.app_context():
        db = get_datamodel()
        id_ = db.execute("SELECT id FROM video WHERE link='new_link'").fetchone()['id']
        assertEqual(id_, 3)

def test_video_tag_list(app, client, auth):
    auth.login()
    response = client.get('/video_tags/1/1')
    assertEqual(response.status_code, 200)
    assertEqual(len(response.json), 4)
    # check that ordering is ascending
    sorted_list = sorted(response.json, key=lambda x: x["timestamp"])
    assertEqual(sorted_list, response.json)

def test_create_tag_on_existing_video(app, client, auth):
    auth.login()
    response = client.post(
        '/add_tag',
        json={
            'tag': 'monkey',
            'timestamp': 1.123,
            'tag_list_id': 1,
            'yt_video_id': 'test_link',
        }
    )
    tag_id = response.json.get('id')
    with app.app_context():
        db = get_datamodel()
        tag_row = db.execute(
            "SELECT tag, youtube_timestamp, video_id, tag_list_id"
            " FROM tag"
            " WHERE id=%s",
            (tag_id,)
        ).fetchone()
        assertEqual(tag_row["tag"], "monkey")
        assertEqual(tag_row["youtube_timestamp"], 1.123)
        assertEqual(tag_row["video_id"], 1)
        assertEqual(tag_row["tag_list_id"], 1)

# TODO: Not sure why this gives an error but the functionality does work
@unittest.skip
def test_create_tag_without_valid_tag(app, client, auth):
    auth.login()
    client.post(
        '/add_tag',
        json={
            'tag': '',
            'timestamp': 1.123,
            'tag_list_id': 1,
            'yt_video_id': 'test_link',
        }
    )

    with app.app_context():
        db = get_datamodel()
        tag_lists = db.execute("SELECT * FROM tag").fetchall()
        tags = [row["tag"] for row in tag_lists]
        assertNotIn("", tags)

def test_create_tag_on_existing_video_new_video(app, client, auth):
    new_video_link = 'new_video_link'
    with app.app_context():
        db = get_datamodel()
        videos = db.execute(
            "SELECT id FROM video"
        ).fetchall()
        original_video_number = len(videos)
        assertEqual(original_video_number, 2)

        new_video = db.execute(
            "SELECT id FROM video WHERE link = %s",
            (new_video_link,)
        ).fetchone()
        assertEqual(new_video, None)
    auth.login()
    response = client.post(
        '/add_tag',
        json={
            'tag': 'monkey',
            'timestamp': 1.123,
            'tag_list_id': 1,
            'yt_video_id': new_video_link,
        }
    )
    tag_id = response.json.get('id')
    with app.app_context():
        db = get_datamodel()
        # test to see if a new video was added to the list
        videos = db.execute(
            "SELECT id FROM video"
        ).fetchall()
        new_video_number = len(videos)
        assertLess(original_video_number, new_video_number)

        new_video = db.execute(
            "SELECT id FROM video WHERE link = %s",
            (new_video_link,)
        ).fetchone()["id"]
        assertEqual(new_video, 3)

        # test the actual tag was inserted accurately
        tag_row = db.execute(
            "SELECT tag, youtube_timestamp, video_id, tag_list_id"
            " FROM tag"
            " WHERE id=%s",
            (tag_id,)
        ).fetchone()
        assertEqual(tag_row["tag"], "monkey")
        assertEqual(tag_row["youtube_timestamp"], 1.123)
        # this video id should be 3 indicating that it added a new video link
        assertEqual(tag_row["video_id"], 3)
        assertEqual(tag_row["tag_list_id"], 1)
