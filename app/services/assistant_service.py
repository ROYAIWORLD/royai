"""Assistant flow for phase-1 voice-to-order handling."""
from __future__ import annotations

from app.extensions import db
from app.models import Room, ServiceRequest, SystemMessage
from app.services import event_service, order_service
from app.services.intent_parser import parse_user_text
from app.utils.serialize import order_to_dict


def _save_message(room_id: str, role: str, content: str) -> SystemMessage:
    message = SystemMessage(room_id=room_id, role=role, content=content)
    db.session.add(message)
    db.session.commit()
    event_service.emit_room(
        "assistant_message",
        room_id,
        {"room_id": room_id, "role": role, "content": content},
    )
    return message


def _create_service_request(room_id: str, request_type: str) -> None:
    service_request = ServiceRequest(room_id=room_id, type=request_type, status="pending")
    db.session.add(service_request)
    db.session.commit()
    event_service.emit_all_surfaces(
        "service_request_created",
        {"request": {"id": service_request.id, "room_id": room_id, "type": request_type}},
        room_id=room_id,
    )


def handle_text(room: Room, text: str, *, source: str = "text") -> dict:
    _save_message(room.id, "user", text)

    result = parse_user_text(text)
    payload: dict[str, object] = {
        "intent": result.intent,
        "entities": result.entities,
        "reply": result.reply,
    }

    if result.intent == "order_menu":
        items = [{"menu_id": item["menu_id"], "qty": item.get("qty", 1)} for item in result.entities.get("items") or []]
        if items:
            order = order_service.create_order(room, source=source, items=items)
            payload["order"] = order_to_dict(order)
            payload["order_id"] = order.id
        else:
            payload["reply"] = "주문 메뉴를 정확히 인식하지 못했어요. 다시 말씀해 주세요."
    elif result.intent == "call_staff":
        _create_service_request(room.id, "call_staff")

    _save_message(room.id, "assistant", str(payload["reply"]))
    event_service.emit_room(
        "assistant_reply",
        room.id,
        {"room_id": room.id, **payload},
    )
    return payload


def handle_voice_text(room: Room, text: str) -> dict:
    return handle_text(room, text, source="voice")
