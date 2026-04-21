from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, url_for

bp = Blueprint("pages", __name__)


@bp.get("/watch")
def watch_demo():
    return render_template("watch.html")


@bp.get("/")
def dashboard():
    return render_template("dashboard.html")


@bp.get("/room")
def room_query():
    rid = (request.args.get("room") or "").strip()
    if rid:
        return redirect(url_for("pages.room_screen", room_id=rid))
    return redirect(url_for("pages.dashboard"))


@bp.get("/room/<room_id>")
def room_screen(room_id: str):
    return render_template("roy_room.html", room_id=room_id)


@bp.get("/kitchen")
def kitchen():
    return render_template("kitchen.html")


@bp.get("/admin")
def admin():
    return render_template("admin.html")
