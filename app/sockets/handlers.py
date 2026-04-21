"""Socket.IO 이벤트. REST와 동일 비즈니스 로직 재사용."""
from __future__ import annotations

from flask_socketio import join_room, leave_room

from app.extensions import db
from app.models import Room
from app.services import assistant_service, order_service


def register_socket_handlers(socketio) -> None:
    @socketio.on("connect")
    def _on_connect():
        pass

    @socketio.on("join_room_channel")
    def _join_room_channel(data):
        rid = (data or {}).get("room_id") or ""
        if not rid:
            return {"ok": False, "error": "room_id_required"}
        join_room(f"room_{rid}")
        return {"ok": True, "room": rid}

    @socketio.on("leave_room_channel")
    def _leave_room_channel(data):
        rid = (data or {}).get("room_id") or ""
        if rid:
            leave_room(f"room_{rid}")
        return {"ok": True}

    @socketio.on("join_kitchen")
    def _join_kitchen():
        join_room("kitchen")
        return {"ok": True, "channel": "kitchen"}

    @socketio.on("join_admin")
    def _join_admin():
        join_room("admin")
        return {"ok": True, "channel": "admin"}

    @socketio.on("send_voice_text")
    def _send_voice_text(data):
        rid = (data or {}).get("room_id") or ""
        text = (data or {}).get("text") or ""
        r = db.session.get(Room, rid)
        if not r or not text.strip():
            return {"ok": False, "error": "invalid_payload"}
        out = assistant_service.handle_voice_text(r, text.strip())
        return {"ok": True, **out}

    @socketio.on("create_order")
    def _create_order(data):
        rid = (data or {}).get("room_id") or ""
        r = db.session.get(Room, rid)
        if not r:
            return {"ok": False, "error": "room_not_found"}
        source = (data or {}).get("source") or "text"
        items = (data or {}).get("items") or []
        if not items:
            return {"ok": False, "error": "items_required"}
        order = order_service.create_order(r, source=source, items=items, session_id=(data or {}).get("session_id"))
        from app.utils.serialize import order_to_dict

        return {"ok": True, "order": order_to_dict(order)}

    @socketio.on("create_service_request")
    def _create_service_request(data):
        from app.models import ServiceRequest
        from app.services import event_service
        from app.utils.serialize import service_request_to_dict

        rid = (data or {}).get("room_id") or ""
        typ = (data or {}).get("type") or ""
        if not rid or not typ:
            return {"ok": False, "error": "invalid_payload"}
        r = db.session.get(Room, rid)
        if not r:
            return {"ok": False, "error": "room_not_found"}
        sr = ServiceRequest(room_id=rid, type=typ, status="pending")
        db.session.add(sr)
        db.session.commit()
        event_service.emit_all_surfaces(
            "service_request_created",
            {"request": service_request_to_dict(sr)},
            room_id=rid,
        )
        return {"ok": True, "request": service_request_to_dict(sr)}

    @socketio.on("update_order_status")
    def _update_order_status(data):
        from app.models import Order
        from app.utils.serialize import order_to_dict

        oid = (data or {}).get("order_id")
        st = (data or {}).get("status") or ""
        force = bool((data or {}).get("force"))
        if oid is None or not st:
            return {"ok": False, "error": "invalid_payload"}
        o = db.session.get(Order, int(oid))
        if not o:
            return {"ok": False, "error": "not_found"}
        ok, msg = order_service.set_order_status(o, st, force=force)
        if not ok:
            return {"ok": False, "error": msg}
        return {"ok": True, "order": order_to_dict(o)}

    @socketio.on("order_confirmed")
    def _legacy_order_confirmed(data):
        """구 플랫폼 데모(watch.html)와 동일한 확인 이벤트."""
        from datetime import datetime, timezone

        from app.routes.compat import notification_log

        if not isinstance(data, dict):
            return
        order_id = data.get("order_id")
        item = data.get("item")
        for row in reversed(notification_log):
            if order_id and row.get("order_id") == order_id:
                row["acked"] = True
                row["ack_ts"] = datetime.now(timezone.utc).isoformat()
                break
        socketio.emit(
            "order_ack_logged",
            {"order_id": order_id, "item": item, "status": "confirmed"},
            namespace="/",
        )
