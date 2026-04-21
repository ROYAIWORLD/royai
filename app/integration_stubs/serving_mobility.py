"""서빙 이동 시스템 연동 스텁."""


def request_delivery_to_room(room_id: str, order_id: int) -> dict:
    return {"ok": True, "stub": True, "room_id": room_id, "order_id": order_id}
