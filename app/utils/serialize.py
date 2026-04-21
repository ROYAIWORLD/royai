from __future__ import annotations

from typing import Any

from app.models import DiningSession, EventLog, Menu, Order, OrderItem, Room, ServiceRequest, SystemMessage


def room_to_dict(r: Room) -> dict[str, Any]:
    return {
        "id": r.id,
        "name": r.name,
        "display_name": r.display_name,
        "status": r.status,
        "is_occupied": r.is_occupied,
        "current_session_id": r.current_session_id,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def menu_to_dict(m: Menu) -> dict[str, Any]:
    return {
        "id": m.id,
        "name": m.name,
        "description": m.description,
        "price": m.price,
        "category": m.category,
        "is_active": m.is_active,
        "sort_order": m.sort_order,
    }


def order_item_to_dict(i: OrderItem) -> dict[str, Any]:
    return {
        "id": i.id,
        "order_id": i.order_id,
        "menu_id": i.menu_id,
        "name_snapshot": i.name_snapshot,
        "qty": i.qty,
        "unit_price": i.unit_price,
        "status": i.status,
        "notes": i.notes,
    }


def order_to_dict(o: Order, include_items: bool = True) -> dict[str, Any]:
    d: dict[str, Any] = {
        "id": o.id,
        "room_id": o.room_id,
        "session_id": o.session_id,
        "status": o.status,
        "source": o.source,
        "total_amount": o.total_amount,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "updated_at": o.updated_at.isoformat() if o.updated_at else None,
    }
    if include_items:
        d["items"] = [order_item_to_dict(i) for i in o.items.order_by(OrderItem.id)]
    return d


def service_request_to_dict(s: ServiceRequest) -> dict[str, Any]:
    return {
        "id": s.id,
        "room_id": s.room_id,
        "type": s.type,
        "status": s.status,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "handled_at": s.handled_at.isoformat() if s.handled_at else None,
    }


def event_log_to_dict(e: EventLog) -> dict[str, Any]:
    return {
        "id": e.id,
        "room_id": e.room_id,
        "event_type": e.event_type,
        "payload": e.get_payload(),
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


def system_message_to_dict(m: SystemMessage) -> dict[str, Any]:
    return {
        "id": m.id,
        "room_id": m.room_id,
        "role": m.role,
        "content": m.content,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def session_to_dict(s: DiningSession) -> dict[str, Any]:
    return {
        "id": s.id,
        "room_id": s.room_id,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "ended_at": s.ended_at.isoformat() if s.ended_at else None,
        "guest_count": s.guest_count,
        "status": s.status,
    }
