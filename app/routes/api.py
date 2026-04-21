from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import DiningSession, EventLog, Menu, Order, Room, ServiceRequest
from app.services import assistant_service, order_service, room_service
from app.utils.serialize import (
    event_log_to_dict,
    menu_to_dict,
    order_to_dict,
    room_to_dict,
    service_request_to_dict,
    session_to_dict,
)

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.get("/rooms")
def api_rooms_list():
    rows = Room.query.order_by(Room.id).all()
    return jsonify({"rooms": [room_to_dict(r) for r in rows]})


@bp.get("/rooms/<room_id>")
def api_room_get(room_id: str):
    r = db.session.get(Room, room_id)
    if not r:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"room": room_to_dict(r)})


@bp.post("/rooms/<room_id>/session")
def api_room_start_session(room_id: str):
    r = db.session.get(Room, room_id)
    if not r:
        return jsonify({"error": "not_found"}), 404
    body = request.get_json(silent=True) or {}
    guest_count = int(body.get("guest_count", 1))
    sid = room_service.start_session(r, guest_count=guest_count)
    sess = db.session.get(DiningSession, sid)
    return jsonify({"ok": True, "session": session_to_dict(sess), "room": room_to_dict(r)}), 201


@bp.patch("/rooms/<room_id>/status")
def api_room_patch_status(room_id: str):
    r = db.session.get(Room, room_id)
    if not r:
        return jsonify({"error": "not_found"}), 404
    body = request.get_json(silent=True) or {}
    new_status = (body.get("status") or "").strip()
    force = bool(body.get("force"))
    if not new_status:
        return jsonify({"error": "status_required"}), 400
    ok, msg = room_service.set_room_status(r, new_status, force=force)
    if not ok:
        return jsonify({"error": msg}), 400
    return jsonify({"ok": True, "room": room_to_dict(r)})


@bp.get("/menu")
def api_menu():
    rows = Menu.query.filter_by(is_active=True).order_by(Menu.sort_order, Menu.id).all()
    return jsonify({"items": [menu_to_dict(m) for m in rows]})


@bp.post("/orders")
def api_orders_create():
    body = request.get_json(silent=True) or {}
    room_id = (body.get("room_id") or "").strip()
    if not room_id:
        return jsonify({"error": "room_id_required"}), 400
    r = db.session.get(Room, room_id)
    if not r:
        return jsonify({"error": "room_not_found"}), 404
    source = (body.get("source") or "text").strip()
    items = body.get("items") or []
    if not isinstance(items, list) or not items:
        return jsonify({"error": "items_required"}), 400
    order = order_service.create_order(r, source=source, items=items, session_id=body.get("session_id"))
    return jsonify({"ok": True, "order": order_to_dict(order)}), 201


@bp.get("/orders")
def api_orders_list():
    q = Order.query
    room_id = request.args.get("room_id")
    status = request.args.get("status")
    if room_id:
        q = q.filter_by(room_id=room_id)
    if status:
        q = q.filter_by(status=status)
    rows = q.order_by(Order.id.desc()).limit(200).all()
    return jsonify({"orders": [order_to_dict(o) for o in rows]})


@bp.get("/orders/<int:order_id>")
def api_order_get(order_id: int):
    o = db.session.get(Order, order_id)
    if not o:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"order": order_to_dict(o)})


@bp.patch("/orders/<int:order_id>/status")
def api_order_patch_status(order_id: int):
    o = db.session.get(Order, order_id)
    if not o:
        return jsonify({"error": "not_found"}), 404
    body = request.get_json(silent=True) or {}
    new_s = (body.get("status") or "").strip()
    force = bool(body.get("force"))
    if not new_s:
        return jsonify({"error": "status_required"}), 400
    ok, msg = order_service.set_order_status(o, new_s, force=force)
    if not ok:
        return jsonify({"error": msg}), 400
    return jsonify({"ok": True, "order": order_to_dict(o)})


@bp.post("/service-requests")
def api_service_request_create():
    body = request.get_json(silent=True) or {}
    room_id = (body.get("room_id") or "").strip()
    typ = (body.get("type") or "").strip()
    if not room_id or not typ:
        return jsonify({"error": "room_id_and_type_required"}), 400
    r = db.session.get(Room, room_id)
    if not r:
        return jsonify({"error": "room_not_found"}), 404
    sr = ServiceRequest(room_id=room_id, type=typ, status="pending")
    db.session.add(sr)
    db.session.commit()
    from app.services import event_service

    event_service.emit_all_surfaces(
        "service_request_created",
        {"request": service_request_to_dict(sr)},
        room_id=room_id,
    )
    return jsonify({"ok": True, "request": service_request_to_dict(sr)}), 201


@bp.get("/service-requests")
def api_service_requests_list():
    q = ServiceRequest.query
    room_id = request.args.get("room_id")
    if room_id:
        q = q.filter_by(room_id=room_id)
    rows = q.order_by(ServiceRequest.id.desc()).limit(200).all()
    return jsonify({"requests": [service_request_to_dict(s) for s in rows]})


@bp.patch("/service-requests/<int:req_id>/status")
def api_service_request_patch(req_id: int):
    sr = db.session.get(ServiceRequest, req_id)
    if not sr:
        return jsonify({"error": "not_found"}), 404
    body = request.get_json(silent=True) or {}
    new_s = (body.get("status") or "").strip()
    if not new_s:
        return jsonify({"error": "status_required"}), 400
    sr.status = new_s
    if new_s in ("completed", "canceled"):
        from app.models.entities import utcnow

        sr.handled_at = utcnow()
    db.session.commit()
    from app.services import event_service

    event_service.emit_all_surfaces(
        "service_request_updated",
        {"request": service_request_to_dict(sr)},
        room_id=sr.room_id,
    )
    return jsonify({"ok": True, "request": service_request_to_dict(sr)})


@bp.post("/assistant/voice-text")
def api_assistant_voice_text():
    body = request.get_json(silent=True) or {}
    room_id = (body.get("room_id") or "").strip()
    text = (body.get("text") or "").strip()
    if not room_id or not text:
        return jsonify({"error": "room_id_and_text_required"}), 400
    r = db.session.get(Room, room_id)
    if not r:
        return jsonify({"error": "room_not_found"}), 404
    result: dict[str, Any] = assistant_service.handle_voice_text(r, text)
    return jsonify({"ok": True, **result})


@bp.post("/assistant/text")
def api_assistant_text():
    body = request.get_json(silent=True) or {}
    room_id = (body.get("room_id") or "").strip()
    text = (body.get("text") or "").strip()
    if not room_id or not text:
        return jsonify({"error": "room_id_and_text_required"}), 400
    r = db.session.get(Room, room_id)
    if not r:
        return jsonify({"error": "room_not_found"}), 404
    result = assistant_service.handle_text(r, text, source="text")
    return jsonify({"ok": True, **result})


@bp.get("/events/recent")
def api_events_recent():
    limit = min(int(request.args.get("limit", "80")), 200)
    rows = EventLog.query.order_by(EventLog.id.desc()).limit(limit).all()
    return jsonify({"events": [event_log_to_dict(e) for e in rows]})
