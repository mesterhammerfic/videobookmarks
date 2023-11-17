import abc
import dataclasses
from typing import List, Sequence

from psycopg import Connection

@dataclasses.dataclass(frozen=True)
class User:
    id: int
    username: str

@dataclasses.dataclass(frozen=True)
class TagList:
    id: int
    name: str
    description: str
    username: str

@dataclasses.dataclass(frozen=True)
class Tag:
    user_id: int
    tag_list_d: int
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
    show: bool

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
    show: bool


class DataModel(abc.ABC):
    @abc.abstractmethod
    def get_user(self, user_id: int) -> User:
        """
        Get all tag_lists.
        """
        ...

    @abc.abstractmethod
    def get_tag_lists(self) -> List[TagList]:
        """
        Get all tag_lists.
        """
        ...

    @abc.abstractmethod
    def get_tag_list(self, tag_list_id: int) -> TagList:
        """
        Get a tag_list.
        """
        ...

    @abc.abstractmethod
    def get_tag_list_tags(self, tag_list_id: int) -> Sequence[GroupedTag]:
        """
        Get all the tags for a given tag list id
        """
        ...

    @abc.abstractmethod
    def get_tag_list_videos(self, tag_list_id: int) -> Sequence[GroupedVideo]:
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
    def create_tag_list(self, user_id: int) -> int:
        """
        Create a new tag_list for a given user id
        return the id of that tag list
        """
        ...

    @abc.abstractmethod
    def create_or_load_yt_video_id(self, yt_link: str) -> int:
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
            video_id: str,
            user_id: int,
    ) -> int:
        """Add a new tag to a video, return the id of that new tag"""
        ...


class PostgresDataModel(DataModel):
    """
    The postgres implementation of the DataModel
    """
    def __init__(self, connection: Connection):
        self._connection = connection

    def register_user(self, username: str, password: str) -> int:
        """
        return the id of the user
        """
        pass

    def get_user(self, user_id: int) -> User:
        pass

    def get_tag_lists(self) -> List[TagList]:
        pass

    def get_tag_list(self, tag_list_id: int) -> TagList:
        pass

    def get_tag_list_tags(self, tag_list_id: int) -> Sequence[GroupedTag]:
        pass

    def get_tag_list_videos(self, tag_list_id: int) -> Sequence[GroupedVideo]:
        pass

    def get_video_tags(self, video_id: int, tag_list_id: int) -> Sequence[Tag]:
        pass

    def create_tag_list(self, user_id: int) -> int:
        pass

    def create_or_load_yt_video_id(self, yt_link: str) -> int:
        pass

    def add_tag(self, tag: str, timestamp: float, tag_list_id: int, video_id: str, user_id: int) -> int:
        pass

