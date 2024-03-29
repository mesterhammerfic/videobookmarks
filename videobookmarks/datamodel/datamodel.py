import abc
import dataclasses
from typing import List, Sequence, Optional

from psycopg import connect
from psycopg.rows import dict_row
from werkzeug.security import generate_password_hash


@dataclasses.dataclass(frozen=True)
class User:
    id: int
    username: str
    password: str


@dataclasses.dataclass(frozen=True)
class TagList:
    id: int
    name: str
    description: str
    username: str
    user_id: int
    created: int
    deleted: bool


@dataclasses.dataclass(frozen=True)
class Tag:
    user_id: int
    tag_list_id: int
    video_id: int
    tag: str
    youtube_timestamp: float


@dataclasses.dataclass(frozen=True)
class GroupedTag:
    """
    A grouped tag contains a summary of how a tag appears
    in a given tag list.
        tag: the name of the tag
        count: how often the tag appears in a tag list
        links: a list of all the youtube video IDs that
                have at least one instance of this tag
        show: a boolean that describes whether a tag should
                be shown to the user. Sometimes tags are not
                shown to the user if they do not meet certain
                filtering criteria.
    """

    tag: str
    count: int
    links: Sequence[str]


@dataclasses.dataclass(frozen=True)
class GroupedVideo:
    """
    A grouped video contains a summary of how a video in relation
    to a tag list.
        link: Youtube ID of the video
        thumbnail: url of video thumbnail
        title: Title of the video according to youtube
        num_tags: the number of tags on that video
        tags: a list of all the unique tags in that video
        show: a boolean that describes whether a video should
                be shown to the user. Sometimes videos are not
                shown to the user if they do not meet certain
                filtering criteria.
    """

    link: str
    thumbnail: str
    title: str
    num_tags: int
    tags: Sequence[str]


class DataModel(abc.ABC):
    @abc.abstractmethod
    def close(self) -> None:
        """
        closes the connection to the database
        """
        ...

    @abc.abstractmethod
    def add_user(self, username: str, password: str) -> Optional[int]:
        """
        return the id of the user
        """
        ...

    @abc.abstractmethod
    def get_user_with_id(self, user_id: int) -> Optional[User]:
        """
        Get the user given an id.
        """
        ...

    @abc.abstractmethod
    def get_user_with_name(self, username: str) -> Optional[User]:
        """
        Get the user given a username.
        """
        ...

    @abc.abstractmethod
    def get_tag_lists(self) -> List[TagList]:
        """
        Get all tag_lists where the deleted column is set to false.
        """
        ...

    @abc.abstractmethod
    def get_tag_list(self, tag_list_id: int) -> Optional[TagList]:
        """
        Get a tag_list.
        """
        ...

    @abc.abstractmethod
    def get_tag_list_tags(
        self,
        tag_list_id: int,
    ) -> Sequence[GroupedTag]:
        """
        Get all the tags for a given tag list id
        """
        ...

    @abc.abstractmethod
    def get_tag_list_videos(
        self,
        tag_list_id: int,
    ) -> Sequence[GroupedVideo]:
        """
        get all videos for a given tag list id
        """
        ...

    @abc.abstractmethod
    def get_video_tags(self, video_id: int, tag_list_id: int) -> Sequence[Tag]:
        """
        :param video_id: the id for the video as it is defined in our database,
                        not the youtube video id
        :return: all the tags for that video that are in the given tag_list,
                sorted by timestamp in ascending order
        """
        ...

    @abc.abstractmethod
    def create_tag_list(
        self,
        name: str,
        description: str,
        user_id: int,
    ) -> Optional[int]:
        """
        Create a new tag_list for a given user id
        return the id of that tag list
        """
        ...

    @abc.abstractmethod
    def load_video_id(self, yt_link: str) -> Optional[int]:
        """
        Check if there is an entry in the video table with the same yt_link
        If not, create an entry for it
        """
        ...

    @abc.abstractmethod
    def create_video_id(
        self, yt_link: str, thumbnail_url: str, title: str
    ) -> Optional[int]:
        """
        Check if there is an entry in the video table with the same yt_link
        If not, create an entry for it
        """
        ...

    @abc.abstractmethod
    def add_tag(
        self,
        tag: str,
        timestamp: float,
        tag_list_id: int,
        video_id: int,
        user_id: int,
    ) -> Optional[int]:
        """Add a new tag to a video, return the id of that new tag"""
        ...

    @abc.abstractmethod
    def delete_tag_list(
        self,
        tag_list_id: int,
    ) -> Optional[int]:
        """
        Mark a tag list as deleted. Does not run an actual delete query on the sql database.
        """
        ...


class PostgresDataModel(DataModel):
    """
    The postgres implementation of the DataModel
    """

    def __init__(self, db_url: str):
        self._connection = connect(
            db_url,
            row_factory=dict_row,
        )

    def close(self) -> None:
        self._connection.close()

    def add_user(self, username: str, password: str) -> Optional[int]:
        """
        return the id of the user
        """
        new_id_row = self._connection.execute(
            (
                "INSERT INTO users (username, password)"
                " VALUES (%s, %s)"
                " RETURNING id"
            ),
            (username, generate_password_hash(password)),
        ).fetchone()
        self._connection.commit()
        if new_id_row is None:
            return None
        # here i ensure that the id is an int
        new_id = int(new_id_row["id"])
        return new_id

    def get_user_with_id(self, user_id: int) -> Optional[User]:
        user = self._connection.execute(
            "SELECT id, username, password FROM users WHERE id = %s",
            (user_id,),
        ).fetchone()
        if user:
            return User(**user)
        else:
            return None

    def get_user_with_name(self, username: str) -> Optional[User]:
        user = self._connection.execute(
            "SELECT id, username, password FROM users WHERE username = %s",
            (username,),
        ).fetchone()
        if user:
            return User(**user)
        else:
            return None

    def get_tag_lists(self) -> List[TagList]:
        tag_lists = self._connection.execute(
            "SELECT tl.id, name, description, user_id, username, created, deleted"
            " FROM tag_list tl JOIN users u ON tl.user_id = u.id"
            " WHERE deleted = false"
            " ORDER BY created DESC"
        ).fetchall()
        return [TagList(**tl) for tl in tag_lists]

    def get_tag_list(self, tag_list_id: int) -> Optional[TagList]:
        tag_list = self._connection.execute(
            "SELECT tl.id, name, description, username, user_id, created, deleted"
            " FROM tag_list tl"
            " JOIN users u ON tl.user_id = u.id"
            " WHERE tl.id = %s",
            (tag_list_id,),
        ).fetchone()
        if tag_list:
            return TagList(**tag_list)
        else:
            return None

    def get_tag_list_tags(
        self,
        tag_list_id: int,
    ) -> Sequence[GroupedTag]:
        statement = (
            "SELECT tag, COUNT(*) as count, ARRAY_AGG(DISTINCT v.link) as links"
            " FROM tag t"
            " JOIN video v on t.video_id = v.id"
            " WHERE tag_list_id = %s"
            " GROUP BY tag"
            " ORDER BY tag ASC"
        )
        arguments = (tag_list_id,)

        tag_list_tags = self._connection.execute(
            statement,
            arguments,
        ).fetchall()

        return [GroupedTag(**tag) for tag in tag_list_tags]

    def get_tag_list_videos(
        self,
        tag_list_id: int,
    ) -> Sequence[GroupedVideo]:
        statement = (
            "SELECT link, thumbnail, title,"
            " COUNT(*) as num_tags,"
            " ARRAY_AGG(DISTINCT tag) as tags"
            " FROM video v"
            " JOIN tag t ON t.video_id = v.id"
            " WHERE t.tag_list_id = %s"
            " GROUP BY link, thumbnail, title"
            " ORDER BY count(*) DESC"
        )
        arguments = (tag_list_id,)

        tag_list_videos = self._connection.execute(
            statement,
            arguments,
        ).fetchall()
        return [GroupedVideo(**video) for video in tag_list_videos]

    def get_video_tags(self, video_id: int, tag_list_id: int) -> Sequence[Tag]:
        tags = self._connection.execute(
            "SELECT"
            "    t.user_id,"
            "    tag_list_id,"
            "    video_id,"
            "    tag,"
            "    youtube_timestamp"
            " FROM tag t"
            " JOIN video v ON v.id = t.video_id"
            " JOIN tag_list tl ON t.tag_list_id = tl.id"
            " WHERE tl.id = %s AND v.id = %s"
            " ORDER BY youtube_timestamp ASC",
            (tag_list_id, video_id),
        ).fetchall()
        return [Tag(**tag) for tag in tags]

    def create_tag_list(
        self, name: str, description: str, user_id: int
    ) -> Optional[int]:
        id_row = self._connection.execute(
            (
                "INSERT INTO tag_list (name, description, user_id)"
                " VALUES (%s, %s, %s)"
                " RETURNING id"
            ),
            (name, description, user_id),
        ).fetchone()
        self._connection.commit()
        if id_row is None:
            return None
        id = int(id_row["id"])
        return id

    def load_video_id(self, yt_link: str) -> Optional[int]:
        id_row = self._connection.execute(
            "SELECT id FROM video WHERE link = %s",
            (yt_link,),
        ).fetchone()
        if not id_row:
            return None
        id = int(id_row["id"])
        return id

    def create_video_id(
        self, yt_link: str, thumbnail_url: str, title: str
    ) -> Optional[int]:
        id_row = self._connection.execute(
            (
                "INSERT INTO video (link, thumbnail, title)"
                " VALUES (%s, %s, %s)"
                " RETURNING id"
            ),
            (yt_link, thumbnail_url, title),
        ).fetchone()
        self._connection.commit()
        if id_row is None:
            return None
        id = int(id_row["id"])
        return id

    def add_tag(
        self, tag: str, timestamp: float, tag_list_id: int, video_id: int, user_id: int
    ) -> Optional[int]:
        tag_id_row = self._connection.execute(
            "INSERT INTO tag"
            " (tag_list_id, video_id, user_id, tag, youtube_timestamp)"
            " VALUES (%s, %s, %s, %s, %s)"
            " RETURNING id",
            (tag_list_id, video_id, user_id, tag, timestamp),
        ).fetchone()
        self._connection.commit()
        if tag_id_row is None:
            return None
        id = int(tag_id_row["id"])
        return id

    def delete_tag_list(self, tag_list_id: int) -> Optional[int]:
        tl = self.get_tag_list(tag_list_id)
        if tl is None:
            raise KeyError(f"The tag list id {tag_list_id} does not exist")
        if not tl.deleted:
            self._connection.execute(
                ("UPDATE tag_list " " SET deleted = true" " WHERE id = %s"),
                (tag_list_id,),
            )
            self._connection.commit()
            return tag_list_id
        else:
            raise KeyError(f"The tag list id {tag_list_id} has already been deleted")
