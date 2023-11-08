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
        " FROM tag_list tl JOIN user u ON tl.user_id = u.id"
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
    tag_list = (
        get_db()
        .execute(
            "SELECT tl.id, name, description, username"
            " FROM tag_list tl"
            " JOIN user u ON tl.user_id = u.id"
            " WHERE tl.id = ?",
            (id,),
        )
        .fetchone()
    )

    if tag_list is None:
        abort(404, f"Post id {id} doesn't exist.")

    return tag_list


def get_tag_list_tags(id):
    """
    :param id: id of tag_list to get
    :return: all the tags in that list
    """
    tag_list_tags = (
        get_db()
        .execute(
            "SELECT DISTINCT tag"
            " FROM tag t JOIN tag_list tl ON t.tag_list_id = t.id"
            " WHERE tl.id = ?",
            (id,),
        )
        .fetchall()
    )

    return tag_list_tags


def get_tag_list_videos(id):
    """
    :param id: id of tag_list to get
    :return: all the videos in that list
    """
    tag_list_videos = (
        get_db()
        .execute(
            "SELECT DISTINCT link"
            " FROM video v"
            " JOIN tag t ON t.video_id = v.id"
            " JOIN tag_list tl ON t.tag_list_id = t.id"
            " WHERE tl.id = ?",
            (id,),
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
    tags = (
        get_db()
        .execute(
            "SELECT tag, youtube_timestamp"
            " FROM tag t"
            " JOIN video v ON v.id = t.video_id"
            " JOIN tag_list tl ON t.tag_list_id = tl.id"
            " WHERE tl.id = ? AND v.id = ?"
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
                "INSERT INTO tag_list (name, description, user_id) VALUES (?, ?, ?)",
                (name, description, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("tag_list.index"))

    return render_template("tag_list/create.html")


def create_or_load_yt_video_id(yt_link: str):
    db = get_db()
    id_row = db.execute(
        "SELECT id FROM video WHERE link = ?",
        (yt_link,),
    ).fetchone()
    if not id_row:
        id_row = db.execute(
            "INSERT INTO video (link) VALUES (?) RETURNING ID",
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
            " VALUES (?, ?, ?, ?, ?)"
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
    tags = get_tag_list_tags(id)
    videos = get_tag_list_videos(id)
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
        tags=tags,
        videos=videos,
        tag_list=tag_list,
    )


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_tag_list(id)
    db = get_db()
    db.execute("DELETE FROM post WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("tag_list.index"))
