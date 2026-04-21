"""초기 룸·메뉴 시드."""
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
        ("room6", "room6", "홀 테이블 A"),
    ]
    for rid, name, disp in rooms:
        db.session.add(
            Room(
                id=rid,
                name=name,
                display_name=disp,
                status="idle",
                is_occupied=False,
            )
        )

    menus: list[tuple[str, str, int, str, int]] = [
        ("한돈 생삼겹", "국내산 한돈 생삼겹 150g", 18000, "메인", 10),
        ("한돈 목살", "한돈 목살 구이", 17000, "메인", 20),
        ("된장찌개", "집 된장 베이스", 8000, "식사", 30),
        ("김치찌개", "묵은지 김치찌개", 9000, "식사", 40),
        ("공기밥", "현미·백미 선택", 1500, "식사", 50),
        ("냉면", "육수 냉면", 10000, "식사", 60),
        ("계란찜", "실온 계란 부드럽게", 6000, "추가", 70),
        ("소주", "대표 소주", 5000, "주류", 80),
        ("맥주", "생맥주/캔", 6000, "주류", 90),
        ("음료수", "탄산·무탄산", 3000, "음료", 100),
    ]
    for name, desc, price, cat, so in menus:
        db.session.add(
            Menu(
                name=name,
                description=desc,
                price=price,
                category=cat,
                is_active=True,
                sort_order=so,
            )
        )

    db.session.commit()
    invalidate_menu_cache()
