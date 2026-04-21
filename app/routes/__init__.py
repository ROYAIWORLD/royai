from flask import Flask

from app.routes import api, compat, pages


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(pages.bp)
    app.register_blueprint(api.bp)
    app.register_blueprint(compat.compat_bp)
