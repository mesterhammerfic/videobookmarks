from flask import Blueprint, Response
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from videobookmarks.auth import login_required
from videobookmarks.db import get_db

bp = Blueprint("tag_list", __name__)

@bp.route("/")
@login_required
def index():
    """
    Ask the user to select or create a tag list
    """
    db = get_db()
    tag_lists = db.execute(
        "SELECT tl.id, name, description, user_id, username"
        " FROM tag_list tl JOIN users u ON tl.user_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    return render_template("tag_list/index.html", tag_lists=tag_lists)


def get_tag_list(id):
    """Get a tag_list.

    Checks that the id exists

    :param id: id of tag_list to get
    :return: the tag_list
    :raise 404: if a post with the given id doesn't exist
    """
    db = get_db()
    tag_list = (
        db.execute(
            "SELECT tl.id, name, description, username"
            " FROM tag_list tl"
            " JOIN users u ON tl.user_id = u.id"
            " WHERE tl.id = %s",
            (id,),
        )
        .fetchone()
    )

    if tag_list is None:
        abort(404, f"Tag list id {id} doesn't exist.")

    return tag_list


@login_required
@bp.route("/get_tags/<int:tag_list_id>", methods=("POST",))
def get_tag_list_tags(tag_list_id):
    """
    :param tag_list_id: id of tag_list to get
    :return: all the tags in that list
    """
    videos = request.json["videoLinks"]
    db = get_db()
    if videos:
        statement = (
            "SELECT tag, COUNT(*) as count, ARRAY_AGG(DISTINCT v.link) as links,"
            " ARRAY_AGG(DISTINCT v.link) && %s AS show"
            " FROM tag t"
            " JOIN video v on t.video_id = v.id"
            " WHERE tag_list_id = %s"
            " GROUP BY tag"
            " ORDER BY ARRAY_AGG(DISTINCT v.link) && %s DESC, count(*) DESC"
        )
    else:
        statement = (
            "SELECT tag, COUNT(*) as count, ARRAY_AGG(DISTINCT v.link) as links, true AS show"
            " FROM tag t"
            " JOIN video v on t.video_id = v.id"
            " WHERE tag_list_id = %s"
            " GROUP BY tag"
            " ORDER BY count(*) DESC"
        )

    if videos:
        arguments = (videos, tag_list_id, videos)
    else:
        arguments = (tag_list_id,)

    tag_list_tags = (
        db.execute(
            statement,
            arguments,
        )
        .fetchall()
    )

    return tag_list_tags


@login_required
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
            "SELECT link, COUNT(*) as num_tags, ARRAY_AGG(DISTINCT tag) as tags, ARRAY_AGG(DISTINCT tag) && %s AS show"
            " FROM video v"
            " JOIN tag t ON t.video_id = v.id"
            " WHERE t.tag_list_id = %s"
            " GROUP BY link"
            " ORDER BY ARRAY_AGG(DISTINCT tag) && %s DESC, count(*) DESC"
        )
    else:
        statement = (
            "SELECT link, COUNT(*) as num_tags, ARRAY_AGG(DISTINCT tag) as tags, true AS show"
            " FROM video v"
            " JOIN tag t ON t.video_id = v.id"
            " WHERE t.tag_list_id = %s"
            " GROUP BY link"
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
@login_required
def get_video_tags(video_id, tag_list_id):
    """
    :param video_id: id of video to get
    :param tag_list_id: id of tag_list to get
    :return: all the tags in that list
    """
    db = get_db()
    tags = (
        db.execute(
            "SELECT tag, youtube_timestamp"
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
        id_row = db.execute(
            "INSERT INTO video (link) VALUES (%s) RETURNING ID",
            (yt_link,),
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
@login_required
def tagging(tag_list_id, yt_video_id):
    """Add a new tag to a video"""
    tag_list = get_tag_list(tag_list_id)
    video_id = create_or_load_yt_video_id(yt_video_id)
    return render_template(
        "tag_list/tagging.html",
        tag_list=tag_list,
        yt_video_id=yt_video_id,
        video_id=video_id,
    )


@bp.route("/<int:id>/view", methods=("GET", "POST"))
@login_required
def view_tag_list(id):
    """View a tag list."""
    tag_list = get_tag_list(id)
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
