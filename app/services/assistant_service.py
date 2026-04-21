"""어시스턴트: 의도 → 주문/서비스요청/메시지."""
from __future__ import annotations

from app.extensions import db
from app.models import Room, ServiceRequest, SystemMessage
from app.services import event_service, order_service
from app.services.intent_parser import parse_user_text


def _save_message(room_id: str, role: str, content: str) -> SystemMessage:
    m = SystemMessage(room_id=room_id, role=role, content=content)
    db.session.add(m)
    db.session.commit()
    event_service.emit_room(
        "assistant_message",
        room_id,
        {"room_id": room_id, "role": role, "content": content},
    )
    return m


def handle_text(room: Room, text: str, *, source: str = "text") -> dict:
    """텍스트 한 줄 처리. 음성 STT 결과도 동일 진입."""
    _save_message(room.id, "user", text)
    result = parse_user_text(text)
    intent = result.intent
    entities = result.entities
    extra: dict = {}

    if intent == "order_menu":
        items_payload = [{"menu_id": x["menu_id"], "qty": x.get("qty", 1)} for x in entities.get("items") or []]
        if items_payload:
            order = order_service.create_order(room, source=source, items=items_payload)
            extra["order_id"] = order.id
    elif intent == "call_staff":
        sr = ServiceRequest(room_id=room.id, type="call_staff", status="pending")
        db.session.add(sr)
        db.session.commit()
        event_service.emit_all_surfaces(
            "service_request_created",
            {"request": {"id": sr.id, "room_id": room.id, "type": sr.type}},
            room_id=room.id,
        )
    elif intent == "request_water":
        sr = ServiceRequest(room_id=room.id, type="water", status="pending")
        db.session.add(sr)
        db.session.commit()
        event_service.emit_all_surfaces(
            "service_request_created",
            {"request": {"id": sr.id, "room_id": room.id, "type": sr.type}},
            room_id=room.id,
        )
    elif intent == "request_napkin":
        sr = ServiceRequest(room_id=room.id, type="napkin", status="pending")
        db.session.add(sr)
        db.session.commit()
        event_service.emit_all_surfaces(
            "service_request_created",
            {"request": {"id": sr.id, "room_id": room.id, "type": sr.type}},
            room_id=room.id,
        )
    elif intent == "request_extra_side":
        sr = ServiceRequest(room_id=room.id, type="extra_side", status="pending")
        db.session.add(sr)
        db.session.commit()
        event_service.emit_all_surfaces(
            "service_request_created",
            {"request": {"id": sr.id, "room_id": room.id, "type": sr.type}},
            room_id=room.id,
        )

    _save_message(room.id, "assistant", result.reply)
    event_service.emit_room(
        "assistant_reply",
        room.id,
        {"room_id": room.id, "intent": intent, "entities": entities, "reply": result.reply, **extra},
    )
    return {"intent": intent, "entities": entities, "reply": result.reply, **extra}


def handle_voice_text(room: Room, text: str) -> dict:
    """STT 결과 텍스트 — 소스 태그만 voice."""
    return handle_text(room, text, source="voice")
