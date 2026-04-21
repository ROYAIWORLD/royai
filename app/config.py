"""RoyAI MVP 설정. 프로덕션은 환경 변수로 덮어쓴다."""
import os


class Config:
    SECRET_KEY = os.environ.get("ROYAI_SECRET_KEY", "royai-mvp-dev-change-me")
    # 템플릿 수정 후 재시작 없이 반영 (프로덕션에서 끄려면 ROYAI_TEMPLATES_AUTO_RELOAD=0)
    TEMPLATES_AUTO_RELOAD = os.environ.get("ROYAI_TEMPLATES_AUTO_RELOAD", "1") != "0"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "ROYAI_DATABASE_URI",
        "sqlite:///" + os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance", "royai_mvp.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SOCKETIO_ASYNC_MODE = os.environ.get("ROYAI_SOCKETIO_ASYNC", "threading")
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.environ.get("ROYAI_SOCKETIO_CORS", "*")
