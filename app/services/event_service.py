"""이벤트 로그 + Socket.IO 브로드캐스트."""
from __future__ import annotations

from typing import Any

from app.extensions import db, socketio
from app.models import EventLog


def log_event(
    event_type: str,
    payload: dict[str, Any],
    room_id: str | None = None,
) -> EventLog:
    row = EventLog(room_id=room_id, event_type=event_type, payload_json="{}")
    row.set_payload(payload)
    db.session.add(row)
    db.session.commit()
    return row


def emit_room(event: str, room_id: str, data: dict[str, Any]) -> None:
    socketio.emit(event, data, room=_room_channel(room_id))


def emit_kitchen(event: str, data: dict[str, Any]) -> None:
    socketio.emit(event, data, room="kitchen")


def emit_admin(event: str, data: dict[str, Any]) -> None:
    socketio.emit(event, data, room="admin")


def emit_all_surfaces(event: str, data: dict[str, Any], room_id: str | None = None) -> None:
    """룸·주방·관제에 공통으로 필요한 이벤트."""
    if room_id:
        emit_room(event, room_id, data)
    emit_kitchen(event, data)
    emit_admin(event, data)


def _room_channel(room_id: str) -> str:
    return f"room_{room_id}"


def broadcast_payload_json(event_type: str, payload: dict[str, Any], room_id: str | None = None) -> None:
    """REST에서도 동일 스키마로 소켓 전파."""
    body = {"event_type": event_type, "payload": payload, "room_id": room_id}
    if room_id:
        emit_room("server_event", room_id, body)
    emit_kitchen("server_event", body)
    emit_admin("server_event", body)
