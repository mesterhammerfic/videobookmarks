from flask import Blueprint
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
        .fetchone()
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
        .fetchone()
    )

    return tag_list_videos


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


def create_or_load_yt_video(yt_link: int):
    db = get_db()
    id = db.execute(
        "SELECT id FROM video WHERE link = ?",
        (yt_link,),
    ).fetchone()["id"]
    if not id:
        id = db.execute(
            "INSERT INTO video (link) VALUES (?) RETURNING ID",
            (yt_link,),
        ).fetchone()["id"]
        db.commit()
    return id


@bp.route("/tagging/<int:tag_list_id>/<string:yt_video_id>", methods=("GET", "POST"))
@login_required
def tagging(tag_list_id, yt_video_id):
    """Add a new tag to a video"""
    tag_list = get_tag_list(tag_list_id)

    if request.method == "POST":
        tag = request.form["tag"]
        timestamp = request.form["timestamp"]
        error = None

        if not tag:
            error = "Tag is required."
        elif not timestamp:
            error = "Timestamp is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            video_id = create_or_load_yt_video(yt_video_id)
            print(video_id)
            db.execute(
                "INSERT INTO tag"
                " (tag_list_id, video_id, user_id, tag, youtube_timestamp)"
                " VALUES (?, ?, ?, ?, ?)",
                (tag_list_id, video_id, g.user["id"], tag, timestamp)
            )
            db.commit()

    return render_template(
        "tag_list/tagging.html",
        tag_list_id=tag_list_id,
        yt_video_id=yt_video_id,
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