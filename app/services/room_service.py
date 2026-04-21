"""룸 상태 FSM."""
from __future__ import annotations

from app.extensions import db
from app.models import Room
from app.services import event_service

ROOM_FSM: dict[str, set[str]] = {
    "idle": {"seated", "cleaning"},
    "seated": {"browsing", "ordering", "idle", "completed"},
    "browsing": {"ordering", "seated", "need_assistance"},
    "ordering": {"waiting_kitchen", "browsing", "need_assistance"},
    "waiting_kitchen": {"cooking", "ordering", "need_assistance"},
    "cooking": {"ready", "need_assistance"},
    "ready": {"serving", "need_assistance"},
    "serving": {"dining", "need_assistance"},
    "dining": {"completed", "ordering", "need_assistance"},
    "need_assistance": {"dining", "ordering", "waiting_kitchen", "seated", "browsing"},
    "completed": {"cleaning", "idle"},
    "cleaning": {"idle"},
}


def can_transition(from_status: str, to_status: str) -> bool:
    allowed = ROOM_FSM.get(from_status)
    if allowed is None:
        return False
    return to_status in allowed


def set_room_status(room: Room, new_status: str, *, force: bool = False) -> tuple[bool, str]:
    if not force and not can_transition(room.status, new_status):
        return False, f"invalid_transition:{room.status}->{new_status}"
    old = room.status
    room.status = new_status
    if new_status in ("idle", "cleaning", "completed") and new_status != "seated":
        pass
    if new_status == "idle":
        room.is_occupied = False
    if new_status in ("seated", "browsing", "ordering", "dining"):
        room.is_occupied = True
    db.session.commit()
    event_service.log_event(
        "room_status_updated",
        {"room_id": room.id, "from": old, "to": new_status},
        room_id=room.id,
    )
    event_service.emit_all_surfaces(
        "room_status_updated",
        {"room": room.id, "from": old, "to": new_status},
        room_id=room.id,
    )
    return True, "ok"


def start_session(room: Room, guest_count: int = 1) -> int:
    from app.models import DiningSession

    sess = DiningSession(room_id=room.id, guest_count=guest_count, status="active")
    db.session.add(sess)
    db.session.flush()
    room.current_session_id = sess.id
    room.is_occupied = True
    if room.status == "idle":
        room.status = "seated"
    db.session.commit()
    event_service.log_event("session_started", {"session_id": sess.id, "room_id": room.id}, room_id=room.id)
    event_service.emit_all_surfaces("room_state", {"room_id": room.id, "session_id": sess.id}, room_id=room.id)
    return sess.id
