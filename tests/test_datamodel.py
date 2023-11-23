from videobookmarks.db import get_datamodel
from werkzeug.security import check_password_hash
from .conftest import CreateTagList


def test_add_user(app):
    with app.app_context():
        datamodel = get_datamodel()
        name = 'test_name'
        password = 'test_password'
        test_user_id = datamodel.add_user(name, password)
        user_row = datamodel._connection.execute(
            (
                "SELECT id, password"
                " FROM users"
                " WHERE username = %s"
            ),
            (name,),
        ).fetchone()
        assert check_password_hash(user_row["password"], password)
        assert test_user_id == user_row["id"]


def test_get_user_with_id(app):
    with app.app_context():
        datamodel = get_datamodel()
        name = 'test_name'
        password = 'test_password'
        test_user_id = datamodel.add_user(name, password)
        user = datamodel.get_user_with_id(test_user_id)
        assert check_password_hash(user.password, password)
        assert name == user.username


def test_get_user_with_name(app):
    with app.app_context():
        datamodel = get_datamodel()
        name = 'test_name'
        password = 'test_password'
        datamodel.add_user(name, password)
        user = datamodel.get_user_with_name(name)
        assert check_password_hash(user.password, password)
        assert name == user.username


def test_create_tag_list(app):
    with app.app_context():
        datamodel = get_datamodel()
        username = "na"
        user_id = datamodel.add_user(username, "na")
        name = 'tag list name'
        desc = 'tag list description'
        tag_list_id = datamodel.create_tag_list(name, desc, user_id)
        tag_list = datamodel.get_tag_list(tag_list_id)
        assert tag_list.username == username
        assert tag_list.user_id == user_id
        assert tag_list.description == desc
        assert tag_list.name == name


def test_add_tag(app):
    with app.app_context():
        tag_list_artifacts = CreateTagList(app)
        datamodel = get_datamodel()
        test_tag = "na"
        test_timestamp = 0
        tag_id = datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts.tag_list_id,
            tag_list_artifacts.video_id,
            tag_list_artifacts.user_id,
        )
        tag = datamodel._connection.execute(
            "SELECT *"
            " FROM tag"
            " WHERE id = %s",
            (tag_id,)
        ).fetchone()
        print(tag)
        assert tag["tag"] == test_tag
        assert tag["youtube_timestamp"] == test_timestamp
        assert tag["tag_list_id"] == tag_list_artifacts.tag_list_id
        assert tag["video_id"] == tag_list_artifacts.video_id
        assert tag["user_id"] == tag_list_artifacts.user_id


def test_get_tag_lists(app):
    with app.app_context():
        tag_list_artifacts_1 = CreateTagList(app, suffix="_1")
        tag_list_artifacts_2 = CreateTagList(app, suffix="_2")
        tag_list_artifacts_3 = CreateTagList(app, suffix="_3")
        datamodel = get_datamodel()
        tag_lists = datamodel.get_tag_lists()
        print(tag_lists)
