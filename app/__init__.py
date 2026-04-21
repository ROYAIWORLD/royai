"""RoyAI MVP Flask 애플리케이션 팩토리."""
from __future__ import annotations

import os

from flask import Flask

from app.config import Config
from app.extensions import db, socketio


def create_app(config_class: type = Config) -> Flask:
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    flask_app = Flask(
        __name__,
        instance_relative_config=False,
        template_folder=os.path.join(pkg_root, "templates"),
        static_folder=os.path.join(pkg_root, "static"),
        static_url_path="/static",
    )
    flask_app.config.from_object(config_class)

    os.makedirs(os.path.join(pkg_root, "instance"), exist_ok=True)

    db.init_app(flask_app)
    socketio.init_app(
        flask_app,
        cors_allowed_origins=flask_app.config["SOCKETIO_CORS_ALLOWED_ORIGINS"],
        async_mode=flask_app.config["SOCKETIO_ASYNC_MODE"],
    )

    with flask_app.app_context():
        import app.models.entities  # noqa: F401 — 모델 등록
        db.create_all()
        from app.seed import seed_if_empty

        seed_if_empty()

    from app.routes import register_blueprints

    register_blueprints(flask_app)

    from app.sockets.handlers import register_socket_handlers

    register_socket_handlers(socketio)

    return flask_app
