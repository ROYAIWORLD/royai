"""주방 도메인 헬퍼 (확장용 얇은 레이어)."""
from __future__ import annotations

from app.models import Order


def filter_orders_for_room(orders: list[Order], room_id: str | None) -> list[Order]:
    if not room_id:
        return orders
    return [o for o in orders if o.room_id == room_id]
