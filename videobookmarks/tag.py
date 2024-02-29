import os
from typing import Sequence, Union

from flask import Blueprint, Response
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from videobookmarks.authenticate import login_required
from videobookmarks.datamodel.datamodel import GroupedTag, GroupedVideo, Tag
from videobookmarks.db import get_datamodel

import requests  # type: ignore

bp = Blueprint("tag", __name__)

YT_API_KEY = os.getenv("YT_API_KEY")
if not YT_API_KEY:
    raise ValueError("YT_API_KEY not set")

TEST_NEW_VIDEO_LINK = "test_new_video_link"


def get_video_details(video_id: str) -> dict[str, str]:
    """
    Get the title and thumbnail of a youtube video
    :param video_id: youtube video id
    :return: dictionary with title and thumbnail_url
    """
    if video_id == TEST_NEW_VIDEO_LINK:
        return {"title": "test_title", "thumbnail_url": "test_thumbnail.url"}
    base_url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "id": video_id,
        "key": YT_API_KEY,
    }

    response = requests.get(base_url, params=params)
    data = response.json()
    if "items" in data and len(data["items"]) > 0:
        video = data["items"][0]
        snippet = video["snippet"]
        title = snippet.get("title", "")
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = thumbnails.get("default", {}).get("url", "")

        if not title:
            raise ValueError("Missing title")
        if not thumbnail_url:
            raise ValueError("Missing thumbnail")

        return {"title": title, "thumbnail_url": thumbnail_url}
    else:
        raise ValueError('data["items"] is empty or missing')


@bp.route("/")  # type: ignore
def index() -> str:
    """
    Ask the user to select or create a tag list
    """
    datamodel = get_datamodel()
    template: str = render_template(
        "tag_list/index.html",
        tag_lists=datamodel.get_tag_lists(),
    )
    return template


@bp.route("/get_tags/<int:tag_list_id>", methods=("GET",))  # type: ignore
def get_tag_list_tags(tag_list_id: int) -> Sequence[GroupedTag]:
    """
    :param tag_list_id: id of tag_list to get
    :return: all the tags in that list
    """
    datamodel = get_datamodel()
    return datamodel.get_tag_list_tags(tag_list_id)


@bp.route("/get_videos/<int:tag_list_id>", methods=("GET",))  # type: ignore
def get_tag_list_videos(tag_list_id: int) -> Sequence[GroupedVideo]:
    """
    :param tag_list_id: id of tag_list to get
    :return: all the videos in that list
    """
    datamodel = get_datamodel()
    return datamodel.get_tag_list_videos(tag_list_id)


@bp.route("/video_tags/<int:video_id>/<int:tag_list_id>", methods=("GET",))  # type: ignore
def get_video_tags(video_id: int, tag_list_id: int) -> Sequence[Tag]:
    """
    :param video_id: id of video to get
    :param tag_list_id: id of tag_list to get
    :return: all the tags in that list that correspond to that video
    """
    datamodel = get_datamodel()
    return datamodel.get_video_tags(video_id, tag_list_id)


@bp.route("/create", methods=("GET", "POST"))  # type: ignore
@login_required  # type: ignore
def create() -> Union[str, Response]:
    """Create a new tag_list for the current user."""
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        user_id = g.user.id

        error = None
        if not name:
            error = "Name is required."

        if error is not None:
            flash(error)
        else:
            datamodel = get_datamodel()
            datamodel.create_tag_list(name, description, user_id)
            return redirect(url_for("tag.index"))

    return render_template("tag_list/create.html")


def create_or_load_yt_video_id(yt_link: str) -> int:
    """
    :param yt_link: youtube link
    :return: video_id as it is stored in our database
    Check if the youtube video is already in our database, if not, add it
    """
    datamodel = get_datamodel()
    video_id = datamodel.load_video_id(yt_link)
    if not video_id:
        video_details = get_video_details(yt_link)
        video_id = datamodel.create_video_id(
            yt_link,
            video_details["thumbnail_url"],
            video_details["title"],
        )
    if video_id is None:
        raise ValueError("video_id is None")
    return video_id


@bp.route("/add_tag", methods=("POST",))  # type: ignore
@login_required  # type: ignore
def add_tag() -> Union[Response, dict[str, int]]:
    """
    Add a new tag to a video
    """
    tag = request.json["tag"]
    timestamp = request.json["timestamp"]
    tag_list_id = request.json["tag_list_id"]
    yt_video_id = request.json["yt_video_id"]
    user_id = g.user.id
    error = None

    if not tag:
        error = "Tag is required."

    if error is not None:
        return Response(422)
    else:
        video_id = create_or_load_yt_video_id(yt_video_id)
        datamodel = get_datamodel()
        tag_id = datamodel.add_tag(
            tag,
            timestamp,
            tag_list_id,
            video_id,
            user_id,
        )
        # TODO: why does this need to return a json? js keeps throwing an error otherwise
        return {"id": tag_id}


@bp.route("/delete_tag_list/<int:tag_list_id>", methods=("DELETE",))  # type: ignore
@login_required  # type: ignore
def delete_tag_list(tag_list_id: int) -> Union[Response, str]:
    """
    Delete a tag list
    :param tag_list_id: id of tag list to delete
    :return: id of deleted tag list
    Note, this does not actually delete the tag list, it just marks it as deleted
    in the database so that it is filtered from the results. Because tags are very
    specific and very time consuming to create, I want to ensure that they are not
    accidentally deleted permanently.
    """
    user_id = g.user.id
    if not tag_list_id:
        error = "Tag list id is required."
        abort(Response(response=[error], status=422))
    datamodel = get_datamodel()
    tag_list = datamodel.get_tag_list(tag_list_id)
    if tag_list is None:
        error = "No tag list with that id found"
        abort(Response(response=[error], status=422))
    if user_id != tag_list.user_id:  # type: ignore
        error = "You are not authorized to delete this tag list"
        abort(Response(response=[error], status=403))
    try:
        deleted_tag_list_id = datamodel.delete_tag_list(tag_list_id)
        return Response(
            response=[f"deleted tag_list id: {deleted_tag_list_id}"],
            status=200,
        )
    except KeyError:
        abort(404)


@bp.route("/tagging/<int:tag_list_id>/<string:yt_video_id>", methods=("GET",))  # type: ignore
def tagging(tag_list_id: int, yt_video_id: str) -> str:
    """
    This is the endpoint that allows the user to watch and tag youtube videos
    :param tag_list_id: id of tag list to tag
    :param yt_video_id: youtube video id
    :return: the tagging page
    """
    datamodel = get_datamodel()
    tag_list = datamodel.get_tag_list(tag_list_id)
    if tag_list is None:
        abort(404, f"Tag list id {id} doesn't exist.")
    video_id = create_or_load_yt_video_id(yt_video_id)
    template: str = render_template(
        "tag_list/tagging.html",
        tag_list=tag_list,
        yt_video_id=yt_video_id,
        video_id=video_id,
    )
    return template


@bp.route("/<int:tag_list_id>/view", methods=("GET", "POST"))  # type: ignore
def view_tag_list(tag_list_id: int) -> Union[Response, str]:
    """
    Renders an interactive page that allows the user to explore the tags and videos
    in a tag list
    :param tag_list_id: id of tag list to view
    :return: the view page or the tagging page if the user submits a new video
    """
    datamodel = get_datamodel()
    tag_list = datamodel.get_tag_list(tag_list_id)
    if tag_list is None:
        abort(404, f"Tag list id {id} doesn't exist.")
    if request.method == "POST":
        yt_video_id = request.form["new_video_id"]
        error = None

        if not yt_video_id:
            error = "Youtube Video ID is required."

        if error is not None:
            flash(error)
        else:
            return redirect(f"/tagging/{tag_list.id}/{yt_video_id}")  # type: ignore
    return render_template(
        "tag_list/view.html",
        tag_list=tag_list,
    )
