"""Rule-based intent parser for the phase-1 ordering MVP."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.extensions import db
from app.models import Menu


@dataclass
class IntentResult:
    intent: str
    entities: dict[str, Any]
    reply: str


_MENU_CACHE: list[dict[str, Any]] | None = None

MENU_SYNONYMS: dict[str, list[str]] = {
    "생삼겹살": ["삼겹살", "삼겹", "생삼겹"],
    "생목살": ["목살", "생목살"],
    "된장찌개": ["된장", "된찌"],
    "김치찌개": ["김치찌개", "김치찌게", "김치"],
    "공기밥": ["밥", "공깃밥", "공기밥"],
    "냉면": ["물냉면", "비빔냉면", "냉면"],
    "계란찜": ["계란찜", "달걀찜"],
    "소주": ["소주"],
    "맥주": ["맥주", "생맥주"],
    "음료수": ["음료", "콜라", "사이다", "탄산"],
}

QUANTITY_WORDS = {
    "한": 1,
    "하나": 1,
    "한개": 1,
    "한잔": 1,
    "두": 2,
    "둘": 2,
    "두개": 2,
    "세": 3,
    "셋": 3,
    "세개": 3,
    "네": 4,
    "넷": 4,
    "네개": 4,
}


def _menus() -> list[dict[str, Any]]:
    global _MENU_CACHE
    if _MENU_CACHE is None:
        rows = (
            db.session.query(Menu.id, Menu.name)
            .filter(Menu.is_active.is_(True))
            .order_by(Menu.sort_order, Menu.id)
            .all()
        )
        _MENU_CACHE = [{"id": int(menu_id), "name": str(name or "")} for menu_id, name in rows]
    return _MENU_CACHE


def invalidate_menu_cache() -> None:
    global _MENU_CACHE
    _MENU_CACHE = None


def strip_wake_prefix(text: str) -> str:
    return re.sub(r"^\s*(로이야|로이)\s*[,!\s]*", "", (text or "").strip(), flags=re.I)


def extract_quantity(text: str) -> int:
    compact = re.sub(r"\s+", "", text or "")
    match = re.search(r"(\d+)(?:인분|개|잔|병|그릇)", compact)
    if match:
        return max(1, int(match.group(1)))

    for word, quantity in QUANTITY_WORDS.items():
        if re.search(rf"{word}(?:인분|개|잔|병|그릇)", compact):
            return quantity

    return 1


def extract_menu_items(text: str) -> list[dict[str, Any]]:
    raw = (text or "").strip()
    if not raw:
        return []

    found: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    quantity = extract_quantity(raw)
    lowered = raw.lower()

    for menu in _menus():
        menu_id = int(menu["id"])
        menu_name = str(menu["name"])
        aliases = [menu_name, *MENU_SYNONYMS.get(menu_name, [])]
        if any(alias and (alias in raw or alias.lower() in lowered) for alias in aliases):
            if menu_id in seen_ids:
                continue
            seen_ids.add(menu_id)
            found.append({"menu_id": menu_id, "name": menu_name, "qty": quantity})

    return found


def detect_intent(text: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return "unknown"

    work = strip_wake_prefix(raw)
    source = work or raw

    if any(keyword in source for keyword in ("직원", "사람", "불러", "호출")):
        return "call_staff"

    if extract_menu_items(source):
        return "order_menu"

    if any(keyword in source for keyword in ("주문", "추가해줘", "갖다줘", "주세요")):
        return "order_menu"

    return "unknown"


def build_assistant_response(intent: str, entities: dict[str, Any]) -> str:
    if intent == "order_menu":
        items = entities.get("items") or []
        if not items:
            return "메뉴를 다시 한 번 말씀해 주세요."
        names = ", ".join(f"{item['name']} {item.get('qty', 1)}개" for item in items)
        return f"{names} 주문을 접수했어요."

    if intent == "call_staff":
        return "직원을 호출했어요."

    return "주문할 메뉴를 말씀해 주세요. 예: 삼겹살 2인분 주문해줘."


def parse_user_text(text: str) -> IntentResult:
    raw = (text or "").strip()
    intent = detect_intent(raw)
    entities: dict[str, Any] = {"raw": raw}

    if intent == "order_menu":
        entities["items"] = extract_menu_items(strip_wake_prefix(raw)) or extract_menu_items(raw)

    reply = build_assistant_response(intent, entities)
    return IntentResult(intent=intent, entities=entities, reply=reply)
