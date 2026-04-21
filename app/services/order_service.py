"""주문 생성·상태."""
from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models import Menu, Order, OrderItem, Room
from app.services import event_service


ORDER_FLOW: dict[str, set[str]] = {
    "created": {"accepted", "canceled"},
    "accepted": {"queued", "canceled"},
    "queued": {"cooking", "canceled"},
    "cooking": {"ready", "canceled"},
    "ready": {"served", "canceled"},
    "served": {"done"},
    "done": set(),
    "canceled": set(),
}


def can_order_transition(from_s: str, to_s: str) -> bool:
    return to_s in ORDER_FLOW.get(from_s, set())


def create_order(
    room: Room,
    *,
    source: str,
    items: list[dict[str, Any]],
    session_id: int | None = None,
) -> Order:
    total = 0
    order = Order(room_id=room.id, session_id=session_id or room.current_session_id, status="created", source=source)
    db.session.add(order)
    db.session.flush()
    for row in items:
        mid = int(row["menu_id"])
        qty = int(row.get("qty", 1))
        menu = db.session.get(Menu, mid)
        if not menu or not menu.is_active:
            continue
        unit = menu.price
        total += unit * qty
        db.session.add(
            OrderItem(
                order_id=order.id,
                menu_id=menu.id,
                name_snapshot=menu.name,
                qty=qty,
                unit_price=unit,
                status="created",
                notes=str(row.get("notes", "") or "")[:256],
            )
        )
    order.total_amount = total
    db.session.commit()
    event_service.log_event(
        "order_created",
        {"order_id": order.id, "room_id": room.id, "total": total},
        room_id=room.id,
    )
    from app.utils.serialize import order_to_dict

    payload = {"order": order_to_dict(order)}
    event_service.emit_all_surfaces("order_created", payload, room_id=room.id)
    event_service.emit_kitchen("kitchen_queue_updated", payload)
    event_service.emit_admin("admin_event", {"type": "order_created", **payload})
    return order


def set_order_status(order: Order, new_status: str, *, force: bool = False) -> tuple[bool, str]:
    if not force and not can_order_transition(order.status, new_status):
        return False, f"invalid_order_transition:{order.status}->{new_status}"
    old = order.status
    order.status = new_status
    for it in order.items:
        if new_status == "canceled":
            it.status = "canceled"
        elif new_status == "accepted" and it.status == "created":
            it.status = "accepted"
        elif new_status == "queued" and it.status in ("created", "accepted"):
            it.status = "queued"
        elif new_status == "cooking":
            it.status = "cooking"
        elif new_status == "ready":
            it.status = "ready"
        elif new_status == "served":
            it.status = "served"
        elif new_status == "done":
            it.status = "done"
    db.session.commit()
    event_service.log_event(
        "order_updated",
        {"order_id": order.id, "from": old, "to": new_status, "room_id": order.room_id},
        room_id=order.room_id,
    )
    from app.utils.serialize import order_to_dict

    body = {"order": order_to_dict(order)}
    event_service.emit_all_surfaces("order_updated", body, room_id=order.room_id)
    event_service.emit_kitchen("kitchen_queue_updated", body)
    return True, "ok"
