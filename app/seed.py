"""Initial room and menu seed data for the MVP."""
from __future__ import annotations

from app.extensions import db
from app.models import Menu, Room
from app.services.intent_parser import invalidate_menu_cache


def seed_if_empty() -> None:
    if Room.query.count() > 0:
        return

    rooms = [
        ("room1", "room1", "룸 1"),
        ("room2", "room2", "룸 2"),
        ("room3", "room3", "룸 3"),
        ("room4", "room4", "룸 4"),
        ("room5", "room5", "VIP 룸"),
        ("room6", "room6", "단체 테이블 A"),
    ]
    for room_id, name, display_name in rooms:
        db.session.add(
            Room(
                id=room_id,
                name=name,
                display_name=display_name,
                status="idle",
                is_occupied=False,
            )
        )

    menus: list[tuple[str, str, int, str, int]] = [
        ("생삼겹살", "국내산 생삼겹살 150g", 18000, "메인", 10),
        ("생목살", "국내산 생목살 150g", 17000, "메인", 20),
        ("된장찌개", "구수한 된장찌개", 8000, "식사", 30),
        ("김치찌개", "진한 김치찌개", 9000, "식사", 40),
        ("공기밥", "추가 공기밥", 1500, "추가", 50),
        ("냉면", "식사 냉면", 10000, "식사", 60),
        ("계란찜", "부드러운 계란찜", 6000, "추가", 70),
        ("소주", "시원한 소주", 5000, "주류", 80),
        ("맥주", "생맥주 또는 병맥주", 6000, "주류", 90),
        ("음료수", "콜라, 사이다 등", 3000, "음료", 100),
    ]
    for name, description, price, category, sort_order in menus:
        db.session.add(
            Menu(
                name=name,
                description=description,
                price=price,
                category=category,
                is_active=True,
                sort_order=sort_order,
            )
        )

    db.session.commit()
    invalidate_menu_cache()
