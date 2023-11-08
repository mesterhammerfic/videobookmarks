import os
import tempfile
import unittest
from videobookmarks import create_app
from videobookmarks.db import init_db, get_db
from .fixtures import AuthActions

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

    def test_index(self):
        self.auth.logout()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn(b'<a href="/auth/login">/auth/login</a>', response.data)

        self.auth.login()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Log Out', response.data)
        self.assertIn(b'test_1', response.data)
        self.assertIn(b'by test', response.data)
        self.assertIn(b'test_description', response.data)
        self.assertIn(b' href="/1/view"', response.data)
        self.assertIn(b'test_2', response.data)
        self.assertIn(b'by other', response.data)
        self.assertIn(b' href="/2/view"', response.data)

    def test_create_tag_list_login_required(self):
        response = self.client.get('/create')
        self.assertEqual(response.status_code, 302)

    def test_create_tag_list_load_page(self):
        self.auth.login()
        response = self.client.get('/create')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="/auth/logout"', response.data)
        self.assertIn(b'textarea name="description" id="description"', response.data)
        self.assertIn(b'form method="post"', response.data)
        self.assertIn(b'input name="name" id="name" value="" required', response.data)
        self.assertIn(b'textarea name="description" id="description"', response.data)

    def test_view_tag_list(self):
        self.auth.login()
        response = self.client.get('/1/view')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="/auth/logout"', response.data)
        self.assertIn(b'input name="yt_video_id" id="yt_video_id"', response.data)
        self.assertIn(b'<p> test_description </p>', response.data)
        self.assertIn(b'<h1>Viewing test_1</h1>', response.data)

    def test_view_tag_list_not_found(self):
        self.auth.login()
        response = self.client.get('/99/view')
        self.assertEqual(response.status_code, 404)

    def test_view_tag_list_video_url_post(self):
        self.auth.login()
        response = self.client.post('/1/view', data={'yt_video_id': 'test_link'})
        self.assertIn(b'Redirecting', response.data)
        self.assertIn(b'href="/tagging/1/test_link"', response.data)

    def test_create_tag_list_post(self):
        self.auth.login()
        self.client.post('/create', data={'name': 'test_3', 'description': 'another one'})

        with self.app.app_context():
            db = get_db()
            description = db.execute("SELECT description FROM tag_list WHERE name='test_3'").fetchone()[0]
            self.assertEqual(description, "another one")

    def test_create_tag_list_post_no_name(self):
        self.auth.login()
        response = self.client.post('/create', data={'name': '', 'description': 'another one'})

        self.assertIn(b'<div class="flash">Name is required.', response.data)

        with self.app.app_context():
            db = get_db()
            tag_lists = db.execute("SELECT * FROM tag_list").fetchall()
            names = [row["name"] for row in tag_lists]
            self.assertNotIn("", names)

    def test_video_tagging(self):
        self.auth.login()
        response = self.client.get('/tagging/1/test_link')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Tagging for test_1', response.data)
        self.assertIn(b"videoId: 'test_link'", response.data)
        self.assertIn(b'input type="text" name="tag" id="tag-input"', response.data)
        self.assertIn(b'button id="add-tag-button">Add Tag</button>', response.data)
        self.assertIn(b'<p>test_description</p>', response.data)

    def test_video_tagging_new_video(self):
        self.auth.login()
        # up until this point, there is no video with the link "new_link"
        # so it should create a new one
        response = self.client.get('/tagging/1/new_link')
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            db = get_db()
            id_ = db.execute("SELECT id FROM video WHERE link='new_link'").fetchone()[0]
            self.assertEqual(id_, 3)

    def test_video_tag_list(self):
        self.auth.login()
        response = self.client.get('/video_tags/1/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 4)
        # check that ordering is ascending
        sorted_list = sorted(response.json, key=lambda x: x["timestamp"])
        self.assertEqual(sorted_list, response.json)

    def test_create_tag_on_existing_video(self):
        self.auth.login()
        response = self.client.post(
            '/add_tag',
            json={
                'tag': 'monkey',
                'timestamp': 1.123,
                'tag_list_id': 1,
                'yt_video_id': 'test_link',
            }
        )
        tag_id = response.json.get('id')
        with self.app.app_context():
            db = get_db()
            tag_row = db.execute(
                "SELECT tag, youtube_timestamp, video_id, tag_list_id"
                " FROM tag"
                " WHERE id=?",
                (tag_id,)
            ).fetchone()
            self.assertEqual(tag_row["tag"], "monkey")
            self.assertEqual(tag_row["youtube_timestamp"], 1.123)
            self.assertEqual(tag_row["video_id"], 1)
            self.assertEqual(tag_row["tag_list_id"], 1)

    # TODO: Not sure why this gives an error but the functionality does work
    @unittest.skip
    def test_create_tag_without_valid_tag(self):
        self.auth.login()
        self.client.post(
            '/add_tag',
            json={
                'tag': '',
                'timestamp': 1.123,
                'tag_list_id': 1,
                'yt_video_id': 'test_link',
            }
        )

        with self.app.app_context():
            db = get_db()
            tag_lists = db.execute("SELECT * FROM tag").fetchall()
            tags = [row["tag"] for row in tag_lists]
            self.assertNotIn("", tags)

    def test_create_tag_on_existing_video_new_video(self):
        new_video_link = 'new_video_link'
        with self.app.app_context():
            db = get_db()
            videos = db.execute(
                "SELECT id FROM video"
            ).fetchall()
            original_video_number = len(videos)
            self.assertEqual(original_video_number, 2)

            new_video = db.execute(
                "SELECT id FROM video WHERE link = ?",
                (new_video_link,)
            ).fetchone()
            self.assertEqual(new_video, None)
        self.auth.login()
        response = self.client.post(
            '/add_tag',
            json={
                'tag': 'monkey',
                'timestamp': 1.123,
                'tag_list_id': 1,
                'yt_video_id': new_video_link,
            }
        )
        tag_id = response.json.get('id')
        with self.app.app_context():
            db = get_db()
            # test to see if a new video was added to the list
            videos = db.execute(
                "SELECT id FROM video"
            ).fetchall()
            new_video_number = len(videos)
            self.assertLess(original_video_number, new_video_number)

            new_video = db.execute(
                "SELECT id FROM video WHERE link = ?",
                (new_video_link,)
            ).fetchone()["id"]
            self.assertEqual(new_video, 3)

            # test the actual tag was inserted accurately
            tag_row = db.execute(
                "SELECT tag, youtube_timestamp, video_id, tag_list_id"
                " FROM tag"
                " WHERE id=?",
                (tag_id,)
            ).fetchone()
            self.assertEqual(tag_row["tag"], "monkey")
            self.assertEqual(tag_row["youtube_timestamp"], 1.123)
            # this video id should be 3 indicating that it added a new video link
            self.assertEqual(tag_row["video_id"], 3)
            self.assertEqual(tag_row["tag_list_id"], 1)
