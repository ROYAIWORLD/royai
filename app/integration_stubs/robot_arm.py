"""조리 로봇팔 연동 스텁."""


def enqueue_cook_task(order_item_id: int, recipe_code: str | None = None) -> dict:
    return {"ok": True, "stub": True, "order_item_id": order_item_id, "recipe_code": recipe_code}
