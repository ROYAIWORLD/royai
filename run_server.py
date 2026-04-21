"""RoyAI 플랫폼 진입점 (SocketIO + Werkzeug, Apache 뒤 127.0.0.1 바인딩 권장)."""

import os

from app import create_app
from app.extensions import socketio

flask_app = create_app()

if __name__ == "__main__":
    host = os.environ.get("BIND", "127.0.0.1")
    port = int(os.environ.get("PORT", "9120"))
    socketio.run(flask_app, host=host, port=port, allow_unsafe_werkzeug=True)
