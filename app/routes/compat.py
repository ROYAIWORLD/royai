"""레거시 단일 파일 app.py와 동일한 계약: POST /order, 알림 로그 API, Socket 이벤트."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, jsonify, request

from app.extensions import socketio

compat_bp = Blueprint("compat", __name__)

notification_log: list[dict[str, Any]] = []


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def extract_order_item(text: str) -> str:
    t = (text or "").strip()
    m = re.search(r"(\S+)\s*주문", t)
    if m:
        return m.group(1).strip()
    return ""


def derive_item_label(raw: str) -> str:
    t = (raw or "").strip()
    if not t:
        return ""
    if "주문" in t:
        return extract_order_item(t) or "주문"
    return t[:80]


@compat_bp.post("/order")
def legacy_order():
    payload = request.get_json(silent=True) or {}
    raw = (payload.get("text") or request.form.get("text") or "").strip()
    if not raw:
        return jsonify({"ok": False, "error": "text_required"}), 400

    item = derive_item_label(raw)
    order_id = str(uuid.uuid4())

    entry: dict[str, Any] = {
        "ts": _now_iso(),
        "message": raw,
        "item": item,
        "order_id": order_id,
        "acked": False,
        "channel": "order",
        "status": "broadcast",
    }
    notification_log.append(entry)

    socketio.emit(
        "new_order",
        {"item": item, "order_id": order_id, "message": raw},
        namespace="/",
    )

    return jsonify(
        {
            "ok": True,
            "accepted": True,
            "item": item,
            "order_id": order_id,
            "text": raw,
        }
    )


@compat_bp.get("/api/notification-log")
def api_notification_log():
    return jsonify({"entries": notification_log[-50:]})
