"""SQLAlchemy 엔티티. MySQL 등으로 URI만 바꾸면 이식 가능."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.String(32), primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    display_name = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="idle")
    is_occupied = db.Column(db.Boolean, nullable=False, default=False)
    current_session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.String(32), db.ForeignKey("rooms.id"), nullable=False)
    started_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    ended_at = db.Column(db.DateTime(timezone=True), nullable=True)
    guest_count = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(24), nullable=False, default="active")  # active | closed


class Menu(db.Model):
    __tablename__ = "menus"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(512), default="")
    price = db.Column(db.Integer, nullable=False, default=0)  # 원 단위 정수
    category = db.Column(db.String(32), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.String(32), db.ForeignKey("rooms.id"), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=True)
    status = db.Column(db.String(24), nullable=False, default="created")
    source = db.Column(db.String(24), nullable=False, default="text")  # voice | text | staff
    total_amount = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    items = db.relationship("OrderItem", backref="order", lazy="dynamic", cascade="all, delete-orphan")


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey("menus.id"), nullable=True)
    name_snapshot = db.Column(db.String(120), nullable=False)
    qty = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(24), nullable=False, default="created")
    notes = db.Column(db.String(256), default="")


class ServiceRequest(db.Model):
    __tablename__ = "service_requests"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.String(32), db.ForeignKey("rooms.id"), nullable=False)
    type = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(24), nullable=False, default="pending")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
    handled_at = db.Column(db.DateTime(timezone=True), nullable=True)


class EventLog(db.Model):
    __tablename__ = "event_logs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.String(32), db.ForeignKey("rooms.id"), nullable=True)
    event_type = db.Column(db.String(64), nullable=False)
    payload_json = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    def set_payload(self, data: dict[str, Any]) -> None:
        self.payload_json = json.dumps(data, ensure_ascii=False)

    def get_payload(self) -> dict[str, Any]:
        try:
            return json.loads(self.payload_json or "{}")
        except json.JSONDecodeError:
            return {}


class SystemMessage(db.Model):
    __tablename__ = "system_messages"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    room_id = db.Column(db.String(32), db.ForeignKey("rooms.id"), nullable=True)
    role = db.Column(db.String(24), nullable=False)  # user | assistant | system
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)
