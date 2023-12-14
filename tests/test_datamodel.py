from videobookmarks.datamodel.datamodel import GroupedTag, GroupedVideo, Tag
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


def test_get_user_no_user_found(app):
    with app.app_context():
        datamodel = get_datamodel()
        name = 'test_name'
        password = 'test_password'
        datamodel.add_user(name, password)
        # the sql database does not contain negative ids
        non_existent_id = -1
        user = datamodel.get_user_with_id(non_existent_id)
        assert user == None
        # and here's a name we haven't added yet
        non_existent_name = "blah blah blah"
        user = datamodel.get_user_with_name(non_existent_name)
        assert user == None


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


def test_get_tag_list_no_tag_list_found(app):
    with app.app_context():
        datamodel = get_datamodel()
        username = "na"
        user_id = datamodel.add_user(username, "na")
        name = 'tag list name'
        desc = 'tag list description'
        datamodel.create_tag_list(name, desc, user_id)
        non_existent_id = -1
        tag_list = datamodel.get_tag_list(non_existent_id)
        assert tag_list == None


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
        expected_tag_lists = [
            tag_list_artifacts_3.expected_tag_list,
            tag_list_artifacts_2.expected_tag_list,
            tag_list_artifacts_1.expected_tag_list,
        ]
        tag_lists = datamodel.get_tag_lists()
        assert tag_lists == expected_tag_lists


def test_get_tag_list_tags(app):
    with app.app_context():
        tag_list_artifacts_0 = CreateTagList(app, suffix='_0')
        tag_list_artifacts_1 = CreateTagList(app, suffix='_1')
        datamodel = get_datamodel()
        test_tag = "na_1"
        test_timestamp = 0
        datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts_0.tag_list_id,
            tag_list_artifacts_0.video_id,
            tag_list_artifacts_0.user_id,
        )
        test_tag = "na_1"
        test_timestamp = 0
        datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts_0.tag_list_id,
            tag_list_artifacts_1.video_id,
            tag_list_artifacts_1.user_id,
        )
        test_tag = "na_2"
        test_timestamp = 0
        datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts_0.tag_list_id,
            tag_list_artifacts_1.video_id,
            tag_list_artifacts_1.user_id,
        )
        tags = datamodel.get_tag_list_tags(tag_list_artifacts_0.tag_list_id)
        expected_tags = [
            GroupedTag(
                tag='na_1',
                count=2,
                links=['youtube link_0', 'youtube link_1'],
            ),
            GroupedTag(
                tag='na_2',
                count=1,
                links=['youtube link_1'],
            ),
        ]
        assert tags == expected_tags


def test_get_tag_list_tags_with_video_list(app):
    with app.app_context():
        tag_list_artifacts_0 = CreateTagList(app, suffix='_0')
        tag_list_artifacts_1 = CreateTagList(app, suffix='_1')
        datamodel = get_datamodel()
        test_tag = "na_1"
        test_timestamp = 0
        datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts_0.tag_list_id,
            tag_list_artifacts_0.video_id,
            tag_list_artifacts_0.user_id,
        )
        test_tag = "na_1"
        test_timestamp = 0
        datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts_0.tag_list_id,
            tag_list_artifacts_1.video_id,
            tag_list_artifacts_1.user_id,
        )
        test_tag = "na_2"
        test_timestamp = 0
        datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts_0.tag_list_id,
            tag_list_artifacts_1.video_id,
            tag_list_artifacts_1.user_id,
        )
        tags = datamodel.get_tag_list_tags(tag_list_artifacts_0.tag_list_id)
        expected_tags = [
            GroupedTag(
                tag='na_1',
                count=2,
                links=['youtube link_0', 'youtube link_1'],
            ),
            GroupedTag(
                tag='na_2',
                count=1,
                links=['youtube link_1'],
            ),
        ]
        assert tags == expected_tags


def test_get_tag_list_videos(app):
    with app.app_context():
        tag_list_artifacts_0 = CreateTagList(app, suffix='_0')
        tag_list_artifacts_1 = CreateTagList(app, suffix='_1')
        datamodel = get_datamodel()
        test_tag = "na_1"
        test_timestamp = 0
        datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts_0.tag_list_id,
            tag_list_artifacts_0.video_id,
            tag_list_artifacts_0.user_id,
        )
        test_tag = "na_1"
        test_timestamp = 0
        datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts_0.tag_list_id,
            tag_list_artifacts_1.video_id,
            tag_list_artifacts_1.user_id,
        )
        test_tag = "na_2"
        test_timestamp = 0
        datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts_0.tag_list_id,
            tag_list_artifacts_1.video_id,
            tag_list_artifacts_1.user_id,
        )
        videos = datamodel.get_tag_list_videos(tag_list_artifacts_0.tag_list_id)
        expected_videos = [
            GroupedVideo(
                link='youtube link_1',
                thumbnail='fakethumbnailurl.com',
                title='fake youtube title',
                num_tags=2,
                tags=['na_1', 'na_2'],
            ),
            GroupedVideo(
                link='youtube link_0',
                thumbnail='fakethumbnailurl.com',
                title='fake youtube title',
                num_tags=1,
                tags=['na_1'],
            )
        ]
        assert videos == expected_videos


def test_get_tag_list_videos_with_tags(app):
    with app.app_context():
        tag_list_artifacts_0 = CreateTagList(app, suffix='_0')
        tag_list_artifacts_1 = CreateTagList(app, suffix='_1')
        datamodel = get_datamodel()
        test_tag = "na_1"
        test_timestamp = 0
        datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts_0.tag_list_id,
            tag_list_artifacts_0.video_id,
            tag_list_artifacts_0.user_id,
        )
        test_tag = "na_1"
        test_timestamp = 0
        datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts_0.tag_list_id,
            tag_list_artifacts_1.video_id,
            tag_list_artifacts_1.user_id,
        )
        test_tag = "na_2"
        test_timestamp = 0
        datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts_0.tag_list_id,
            tag_list_artifacts_1.video_id,
            tag_list_artifacts_1.user_id,
        )
        videos = datamodel.get_tag_list_videos(tag_list_artifacts_0.tag_list_id)
        expected_videos = [
            GroupedVideo(
                link='youtube link_1',
                thumbnail='fakethumbnailurl.com',
                title='fake youtube title',
                num_tags=2,
                tags=['na_1', 'na_2'],
            ),
            GroupedVideo(
                link='youtube link_0',
                thumbnail='fakethumbnailurl.com',
                title='fake youtube title',
                num_tags=1,
                tags=['na_1'],
            )
        ]
        assert videos == expected_videos


def test_get_video_tags(app):
    with app.app_context():
        tag_list_artifacts_0 = CreateTagList(app, suffix='_0')
        tag_list_artifacts_1 = CreateTagList(app, suffix='_1')
        datamodel = get_datamodel()

        # combo 1
        test_tag = "na_1"
        test_timestamp = 0
        datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts_0.tag_list_id,
            tag_list_artifacts_0.video_id,
            tag_list_artifacts_0.user_id,
        )
        tags_0 = datamodel.get_video_tags(
            tag_list_artifacts_0.video_id,
            tag_list_artifacts_0.tag_list_id,
        )
        expected_tags_0 = [
            Tag(
                user_id=tag_list_artifacts_0.user_id,
                tag_list_id=tag_list_artifacts_0.tag_list_id,
                video_id=tag_list_artifacts_0.video_id,
                tag='na_1',
                youtube_timestamp=0.0
            ),
        ]
        assert tags_0 == expected_tags_0

        # combo 2
        test_tag = "na_1"
        test_timestamp = 0
        datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts_0.tag_list_id,
            tag_list_artifacts_1.video_id,
            tag_list_artifacts_1.user_id,
        )
        tags_1 = datamodel.get_video_tags(
            tag_list_artifacts_1.video_id,
            tag_list_artifacts_0.tag_list_id,
        )
        expected_tags_1 = [
            Tag(
                user_id=tag_list_artifacts_1.user_id,
                tag_list_id=tag_list_artifacts_0.tag_list_id,
                video_id=tag_list_artifacts_1.video_id,
                tag='na_1',
                youtube_timestamp=0.0
            ),
        ]
        assert tags_1 == expected_tags_1

        # combo 3
        test_tag = "na_2"
        test_timestamp = 0
        datamodel.add_tag(
            test_tag,
            test_timestamp,
            tag_list_artifacts_1.tag_list_id,
            tag_list_artifacts_1.video_id,
            tag_list_artifacts_1.user_id,
        )
        tags_2 = datamodel.get_video_tags(
            tag_list_artifacts_1.video_id,
            tag_list_artifacts_1.tag_list_id,
        )
        expected_tags_2 = [
            Tag(
                user_id=tag_list_artifacts_1.user_id,
                tag_list_id=tag_list_artifacts_1.tag_list_id,
                video_id=tag_list_artifacts_1.video_id,
                tag='na_2',
                youtube_timestamp=0.0
            ),
        ]
        assert tags_2 == expected_tags_2


def test_load_video_id(app):
    with app.app_context():
        datamodel = get_datamodel()
        link = "abc123"
        expected_video_id = datamodel.create_video_id(
            link,
            "fakethumbnailurl.com",
            "fake youtube title",
        )
        actual_video_id = datamodel.load_video_id(link)
        assert actual_video_id == expected_video_id


def test_load_video_id_no_id_found(app):
    with app.app_context():
        datamodel = get_datamodel()
        link = "abc123"
        expected_video_id = datamodel.create_video_id(
            link,
            "fakethumbnailurl.com",
            "fake youtube title",
        )
        fake_video_link = "nonexistant_link"
        actual_video_id = datamodel.load_video_id(fake_video_link)
        assert actual_video_id == None


def test_delete_tag_list(app):
    with app.app_context():
        artifacts = CreateTagList(app)
        tag_list_id = artifacts.tag_list_id
        datamodel = get_datamodel()
        datamodel.delete_tag_list(tag_list_id)
        check_existing_tag_lists = datamodel.get_tag_list(tag_list_id)
        check_delete_tag_lists = datamodel.get_deleted_tag_list(tag_list_id)
        assert check_existing_tag_lists == None
        assert check_delete_tag_lists == artifacts.expected_tag_list