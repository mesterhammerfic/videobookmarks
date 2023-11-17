import os

from flask import Blueprint, Response, current_app
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from videobookmarks.auth import login_required
from videobookmarks.datamodel.datamodel import DataModel
from videobookmarks.db import get_db

import requests

bp = Blueprint("tag_list", __name__)

datamodel: DataModel = current_app.config["datamodel"]

YT_API_KEY = os.getenv("YT_API_KEY")
if not YT_API_KEY:
    raise ValueError("YT_API_KEY not set")


def get_video_details(video_id):
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

        return {
            "title": title,
            "thumbnail_url": thumbnail_url
        }
    else:
        raise ValueError('data["items"] is empty or missing')


@bp.route("/")
def index():
    """
    Ask the user to select or create a tag list
    """
    return render_template(
        "tag_list/index.html",
        tag_lists=datamodel.get_tag_lists()
    )


@bp.route("/get_tags/<int:tag_list_id>", methods=("POST",))
def get_tag_list_tags(tag_list_id):
    """
    :param tag_list_id: id of tag_list to get
    :return: all the tags in that list
    """
    yt_videos_ids = request.json["videoLinks"]
    datamodel.get_tag_list_tags(tag_list_id, yt_videos_ids)



@bp.route("/get_videos/<int:tag_list_id>", methods=("POST",))
def get_tag_list_videos(tag_list_id):
    """
    :param tag_list_id: id of tag_list to get
    :return: all the videos in that list
    """
    tags = request.json["tags"]
    db = get_db()
    if tags:
        statement = (
            "SELECT link, thumbnail, title,"
            " COUNT(*) as num_tags,"
            " ARRAY_AGG(DISTINCT tag) as tags,"
            " ARRAY_AGG(DISTINCT tag) && %s AS show"
            " FROM video v"
            " JOIN tag t ON t.video_id = v.id"
            " WHERE t.tag_list_id = %s"
            " GROUP BY link, thumbnail, title"
            " ORDER BY ARRAY_AGG(DISTINCT tag) && %s DESC, count(*) DESC"
        )
    else:
        statement = (
            "SELECT link, thumbnail, title,"
            " COUNT(*) as num_tags,"
            " ARRAY_AGG(DISTINCT tag) as tags,"
            " true AS show"
            " FROM video v"
            " JOIN tag t ON t.video_id = v.id"
            " WHERE t.tag_list_id = %s"
            " GROUP BY link, thumbnail, title"
            " ORDER BY count(*) DESC"
        )

    if tags:
        arguments = (tags, tag_list_id, tags)
    else:
        arguments = (tag_list_id,)

    tag_list_videos = (
        db.execute(
            statement,
            arguments,
        )
        .fetchall()
    )

    return tag_list_videos


@bp.route("/video_tags/<int:video_id>/<int:tag_list_id>", methods=("GET",))
def get_video_tags(video_id, tag_list_id):
    """
    :param video_id: id of video to get
    :param tag_list_id: id of tag_list to get
    :return: all the tags in that list
    """
    db = get_db()
    tags = (
        db.execute(
            "SELECT"
            "    user_id,"
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
        )
        .fetchall()
    )
    return [{"tag": row["tag"], "timestamp": row["youtube_timestamp"]} for row in tags]


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new tag_list for the current user."""
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        error = None

        if not name:
            error = "Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO tag_list (name, description, user_id) VALUES (%s, %s, %s)",
                (name, description, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("tag_list.index"))

    return render_template("tag_list/create.html")


def create_or_load_yt_video_id(yt_link: str):
    db = get_db()
    id_row = db.execute(
        "SELECT id FROM video WHERE link = %s",
        (yt_link,),
    ).fetchone()
    if not id_row:
        video_details = get_video_details(yt_link)
        id_row = db.execute(
            "INSERT INTO video (link, thumbnail, title) VALUES (%s, %s, %s) RETURNING ID",
            (yt_link, video_details["thumbnail_url"], video_details["title"]),
        ).fetchone()
        db.commit()
    return id_row["id"]


@bp.route("/add_tag", methods=("POST",))
@login_required
def add_tag():
    """Add a new tag to a video"""

    tag = request.json["tag"]
    timestamp = request.json["timestamp"]
    tag_list_id = request.json["tag_list_id"]
    yt_video_id = request.json["yt_video_id"]
    error = None

    if not tag:
        error = "Tag is required."

    if error is not None:
        flash(error)
        return Response(422)
    else:
        db = get_db()
        video_id = create_or_load_yt_video_id(yt_video_id)
        tag_id_row = db.execute(
            "INSERT INTO tag"
            " (tag_list_id, video_id, user_id, tag, youtube_timestamp)"
            " VALUES (%s, %s, %s, %s, %s)"
            " RETURNING id",
            (tag_list_id, video_id, g.user["id"], tag, timestamp)
        ).fetchone()
        db.commit()
        # TODO: why does this need to be a blank json? js keeps throwing an error otherwise
        return {"id": tag_id_row["id"]}


@bp.route("/tagging/<int:tag_list_id>/<string:yt_video_id>", methods=("GET", "POST"))
def tagging(tag_list_id, yt_video_id):
    """Add a new tag to a video"""
    tag_list = datamodel.get_tag_list(tag_list_id)
    if tag_list is None:
        abort(404, f"Tag list id {id} doesn't exist.")
    video_id = create_or_load_yt_video_id(yt_video_id)
    return render_template(
        "tag_list/tagging.html",
        tag_list=tag_list,
        yt_video_id=yt_video_id,
        video_id=video_id,
    )


@bp.route("/<int:tag_list_id>/view", methods=("GET", "POST"))
def view_tag_list(tag_list_id):
    """View a tag list."""
    tag_list = datamodel.get_tag_list(tag_list_id)
    if tag_list is None:
        abort(404, f"Tag list id {id} doesn't exist.")
    if request.method == "POST":
        yt_video_id = request.form["yt_video_id"]
        error = None

        if not yt_video_id:
            error = "Youtube Video ID is required."

        if error is not None:
            flash(error)
        else:
            return redirect(
                f"/tagging/{tag_list['id']}/{yt_video_id}"
            )
    return render_template(
        "tag_list/view.html",
        tag_list=tag_list,
    )
