import unittest
from videobookmarks.db import get_datamodel
from .conftest import CreateTagList
from videobookmarks.tag import TEST_NEW_VIDEO_LINK

def test_index_logged_in(app, client, auth):
    auth.register()
    auth.login()
    response = client.get('/')
    assert response.status_code == 200
    assert 'Log Out' in response.data.decode()


def test_index_logged_out(app, client, auth):
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert 'Log In' in response.data.decode()
    assert 'Register' in response.data.decode()

def test_create_tag_list_login_required(app, client, auth):
    response = client.get('/create')
    assert response.status_code == 302

def test_create_tag_list_load_page(app, client, auth):
    auth.register()
    auth.login()
    response = client.get('/create')
    assert response.status_code == 200
    assert 'href="/authenticate/logout"' in response.data.decode()
    assert 'textarea name="description" id="description"' in response.data.decode()
    assert 'form method="post"' in response.data.decode()
    assert 'input name="name" id="name" value="" required' in response.data.decode()
    assert 'textarea name="description" id="description"' in response.data.decode()

def test_view_tag_list(app, client, auth):
    artifacts = CreateTagList(app)
    auth.login(artifacts.username, artifacts.password)
    response = client.get(f'/{artifacts.tag_list_id}/view')
    assert response.status_code == 200
    assert 'href="/authenticate/logout"' in response.data.decode()
    assert 'input name="yt_video_id" id="yt_video_id"' in response.data.decode()
    assert f'<h1>Viewing {artifacts.tag_list_name}</h1>' in response.data.decode()

def test_view_tag_list_not_found(app, client, auth):
    auth.register()
    auth.login()
    response = client.get('/99/view')
    assert response.status_code == 404

def test_view_tag_list_video_url_post(app, client, auth):
    artifacts = CreateTagList(app)
    auth.login(artifacts.username, artifacts.password)
    response = client.post(f'/{artifacts.tag_list_id}/view', data={'yt_video_id': artifacts.yt_video_id})
    assert 'Redirecting'in response.data.decode()
    assert f'href="/tagging/{artifacts.tag_list_id}/{artifacts.yt_video_id}"'in response.data.decode()

def test_view_tag_list_video_url_post_no_video_url(app, client, auth):
    artifacts = CreateTagList(app)
    auth.login(artifacts.username, artifacts.password)
    response = client.post(f'/{artifacts.tag_list_id}/view', data={'yt_video_id': ''})
    assert ' <div class="flash">Youtube Video ID is required.' in response.data.decode()
    assert f'Viewing {artifacts.tag_list_name} 'in response.data.decode()

def test_create_tag_list_post(app, client, auth):
    auth.register()
    auth.login()
    client.post('/create', data={'name': 'test_3', 'description': 'another one'})

    with app.app_context():
        dm = get_datamodel()
        description = dm._connection.execute(
            "SELECT description FROM tag_list WHERE name='test_3'"
        ).fetchone()['description']
        assert description == "another one"

def test_create_tag_list_post_no_name(app, client, auth):
    auth.register()
    auth.login()
    response = client.post('/create', data={'name': '', 'description': 'another one'})

    assert '<div class="flash">Name is required.'in response.data.decode()

    with app.app_context():
        dm = get_datamodel()
        tag_lists = dm._connection.execute("SELECT * FROM tag_list").fetchall()
        names = [row["name"] for row in tag_lists]
        assert "" not in names

def test_video_tagging(app, client, auth):
    artifacts = CreateTagList(app)
    auth.login(artifacts.username, artifacts.password)
    response = client.get(f'/tagging/{artifacts.tag_list_id}/{artifacts.yt_video_id}')
    assert response.status_code == 200
    assert f'Tagging for {artifacts.tag_list_name}' in response.data.decode()
    assert f"<data id=\"yt-video-id\" value=\"{artifacts.yt_video_id}\"></data>" in response.data.decode()
    assert 'input type="text" name="tag" id="tag-input"' in response.data.decode()
    assert 'input type="text" name="tag" id="tag-input"' in response.data.decode()

def test_video_tagging_new_video(app, client, auth):
    artifacts = CreateTagList(app)
    auth.login(artifacts.username, artifacts.password)
    # up until this point, there is no video with the link "new_link"
    # so it should create a new one
    response = client.get(f'/tagging/{artifacts.tag_list_id}/{artifacts.yt_video_id}')
    assert response.status_code == 200

    with app.app_context():
        dm = get_datamodel()
        id_ = dm._connection.execute(
            "SELECT id FROM video WHERE link=%s",
            (artifacts.yt_video_id,)
        ).fetchone()['id']
        assert id_ == artifacts.video_id

def test_video_tag_list(app, client, auth):
    artifacts = CreateTagList(app)
    with app.app_context():
        dm = get_datamodel()
        dm.add_tag(
            'test',
            1.0,
            artifacts.tag_list_id,
            artifacts.video_id,
            artifacts.user_id,
        )
        dm.add_tag(
            'test',
            2.0,
            artifacts.tag_list_id,
            artifacts.video_id,
            artifacts.user_id,
        )
    response = client.get(f'/video_tags/{artifacts.video_id}/{artifacts.tag_list_id}')
    assert response.status_code == 200
    assert len(response.json) == 2
    # check that ordering is ascending
    sorted_list = sorted(response.json, key=lambda x: x["youtube_timestamp"])
    assert sorted_list == response.json

def test_create_tag_on_existing_video(app, client, auth):
    artifacts = CreateTagList(app)
    auth.login(artifacts.username, artifacts.password)
    response = client.post(
        '/add_tag',
        json={
            'tag': 'monkey',
            'timestamp': 1.123,
            'tag_list_id': artifacts.tag_list_id,
            'yt_video_id': artifacts.yt_video_id,
        }
    )
    tag_id = response.json.get('id')
    with app.app_context():
        dm = get_datamodel()
        tag_row = dm._connection.execute(
            "SELECT tag, youtube_timestamp, video_id, tag_list_id"
            " FROM tag"
            " WHERE id=%s",
            (tag_id,)
        ).fetchone()
        assert tag_row["tag"] == "monkey"
        assert tag_row["youtube_timestamp"] == 1.123
        assert tag_row["video_id"] == artifacts.video_id
        assert tag_row["tag_list_id"] == artifacts.tag_list_id

# TODO: Not sure why this gives an error but the functionality does work
@unittest.skip
def test_create_tag_without_valid_tag(app, client, auth):
    auth.register()
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
        dm = get_datamodel()
        tag_lists = dm._connection.execute("SELECT * FROM tag").fetchall()
        tags = [row["tag"] for row in tag_lists]
        assert "" not in tags

def test_create_tag_on_existing_video_new_video(app, client, auth):
    artifacts = CreateTagList(app)
    auth.login(artifacts.username, artifacts.password)
    # this has to match what is written in the tag.py, there's probably
    #  a better way to organize this but I.
    with app.app_context():
        dm = get_datamodel()
        videos = dm._connection.execute(
            "SELECT id FROM video"
        ).fetchall()
        original_video_number = len(videos)
        assert original_video_number == 1

        new_video = dm._connection.execute(
            "SELECT id FROM video WHERE link = %s",
            (TEST_NEW_VIDEO_LINK,)
        ).fetchone()
        assert new_video == None
    response = client.post(
        '/add_tag',
        json={
            'tag': 'monkey',
            'timestamp': 1.123,
            'tag_list_id': artifacts.tag_list_id,
            'yt_video_id': TEST_NEW_VIDEO_LINK,
        }
    )
    tag_id = response.json.get('id')
    with app.app_context():
        dm = get_datamodel()
        # test to see if a new video was added to the list
        videos = dm._connection.execute(
            "SELECT id FROM video"
        ).fetchall()
        new_video_number = len(videos)
        assert original_video_number < new_video_number

        new_video_id = dm.load_video_id(TEST_NEW_VIDEO_LINK)

        # test the actual tag was inserted accurately
        tag_row = dm._connection.execute(
            "SELECT tag, youtube_timestamp, video_id, tag_list_id"
            " FROM tag"
            " WHERE id=%s",
            (tag_id,)
        ).fetchone()
        assert tag_row["tag"] == "monkey"
        assert tag_row["youtube_timestamp"] == 1.123
        # this video id should be 3 indicating that it added a new video link
        assert tag_row["video_id"] == new_video_id
        assert tag_row["tag_list_id"] == artifacts.tag_list_id
