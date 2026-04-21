"""Gunicorn 등 WSGI 진입점. WebSocket은 geventwebsocket 워커 필요."""

from app import create_app

flask_app = create_app()

# gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -b 0.0.0.0:9120 "wsgi:flask_app"
application = flask_app
