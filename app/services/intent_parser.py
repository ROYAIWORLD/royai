"""
규칙 기반 의도 파서 (MVP).
향후 LLM/STT 연동 시 이 모듈 앞단에 어댑터만 두면 된다.
"""
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


def _menus() -> list[dict[str, Any]]:
    global _MENU_CACHE
    if _MENU_CACHE is None:
        # ORM 객체 자체를 캐시하면 commit 후 detached/expired 로드 에러가 날 수 있어
        # 의도 파싱에는 필요한 최소 필드만 평문(dict)으로 캐시한다.
        rows = (
            db.session.query(Menu.id, Menu.name)
            .filter(Menu.is_active.is_(True))
            .order_by(Menu.sort_order, Menu.id)
            .all()
        )
        _MENU_CACHE = [{"id": int(mid), "name": str(name or "")} for mid, name in rows]
    return _MENU_CACHE


# 시드 메뉴명 ↔ 자연어 별칭 (MVP)
MENU_SYNONYMS: dict[str, list[str]] = {
    "한돈 생삼겹": ["삼겹살", "생삼겹", "한돈"],
    "한돈 목살": ["목살"],
    "된장찌개": ["된장"],
    "김치찌개": ["김치"],
    "공기밥": ["밥", "공기"],
    "냉면": [],
    "계란찜": ["계란"],
    "소주": [],
    "맥주": [],
    "음료수": ["음료", "콜라", "사이다"],
}


def invalidate_menu_cache() -> None:
    global _MENU_CACHE
    _MENU_CACHE = None


def extract_quantity(text: str) -> int:
    t = text.strip()
    m = re.search(r"(\d+)\s*(?:인분|개|병|그릇|접시|인|명)?", t)
    if m:
        return max(1, int(m.group(1)))
    if re.search(r"(하나|한\s*개|한\s*병|한\s*그릇)", t):
        return 1
    if re.search(r"(둘|두\s*개|이\s*인분)", t):
        return 2
    return 1


def strip_wake_prefix(text: str) -> str:
    """'로이야', '로이' 등 호출어를 앞에서 제거해 본문만 남긴다. 한 문장에 같이 말할 때 사용."""
    t = (text or "").strip()
    for _ in range(3):
        m = re.match(
            r"^(로이야|로이|루이야|루이|야\s*로이|야\s*루이|헤이\s*로이|헤이\s*루이|hey\s*roy)\s*[,:]?\s*",
            t,
            re.I,
        )
        if not m:
            break
        t = t[m.end() :].strip()
    return t


def is_wake_only_utterance(raw: str) -> bool:
    """로이를 부르기만 한 경우(추가 요청 없음)."""
    s = raw.strip()
    if not s:
        return False
    rest = strip_wake_prefix(s)
    if rest:
        return False
    return bool(
        re.match(
            r"^(로이야|로이|루이야|루이|야\s*로이|야\s*루이|헤이\s*로이|헤이\s*루이|hey\s*roy)([\s!?.~♡]*)$",
            s,
            re.I,
        )
    )


def extract_menu_items(text: str) -> list[dict[str, Any]]:
    """메뉴 DB 이름·별칭으로 품목 추출."""
    found: list[dict[str, Any]] = []
    raw = text.strip()
    if not raw:
        return found
    low = raw.lower()
    for m in _menus():
        menu_name = m.get("name", "")
        menu_id = m.get("id")
        if not menu_name or menu_id is None:
            continue
        if menu_name in raw or menu_name.lower() in low:
            found.append({"menu_id": menu_id, "name": menu_name, "qty": extract_quantity(raw)})
            continue
        for alias in MENU_SYNONYMS.get(menu_name, []):
            if alias and alias in raw:
                found.append({"menu_id": menu_id, "name": menu_name, "qty": extract_quantity(raw)})
                break
    return found


def detect_intent(text: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return "unknown"
    work = strip_wake_prefix(raw)
    low = raw.lower()
    wlow = work.lower()

    # 호출만 한 경우 (예: "로이야", "야 로이")
    if is_wake_only_utterance(raw):
        return "assistant_wake"
    # "로이야 안녕" / "로이야 대답해" 처럼 깨우기 발화
    if work and re.match(r"^(안녕|안녕하세요|하이|hello|hi|대답해|응답해|말해|말해봐|듣고\s*있어)[\s!?.]*$", work, re.I):
        return "assistant_wake"

    # 서비스·주문 키워드는 호출어 제거 뒤 본문(work) 우선
    src = work if work else raw

    if any(k in src for k in ("직원", "사장", "불러", "호출")):
        return "call_staff"
    if "물" in src or "물좀" in wlow.replace(" ", ""):
        return "request_water"
    if "수저" in src or "냅킨" in src or "휴지" in src:
        return "request_napkin"
    if ("반찬" in src) or ("추가" in src and "메뉴" not in src):
        return "request_extra_side"
    if any(k in src for k in ("취소", "안 할래", "그만")):
        return "cancel_order"
    if any(k in src for k in ("뭐였", "주문 내역", "방금")):
        return "order_history"
    if "추천" in src:
        return "recommend"
    if any(k in src for k in ("메뉴 보여", "메뉴 열", "메뉴판 보여", "메뉴 알려", "메뉴 띄")):
        return "show_menu"
    if any(k in src for k in ("메뉴 닫", "메뉴 숨", "메뉴 내려", "메뉴 치워")):
        return "hide_menu"
    if any(k in src for k in ("응", "네", "좋아", "그래", "확인")) and len(src) <= 8:
        return "confirm_yes"

    # 메뉴: "삼겹살 주문해줘" 또는 "로이야 삼겹살 주문해줘" 모두
    if extract_menu_items(work) or extract_menu_items(raw):
        return "order_menu"

    # 품목명이 없어도 주문 의도 문장은 주문 플로우로 연결
    if any(k in src for k in ("주문", "시켜", "시켜줘", "먹을래", "추가해줘")):
        return "order_menu"

    return "unknown"


def build_assistant_response(intent: str, entities: dict[str, Any]) -> str:
    if intent == "assistant_wake":
        return "네."
    if intent == "order_menu":
        items = entities.get("items") or []
        if not items:
            return "어떤 메뉴를 주문하실지 다시 한번 말씀해 주시겠어요?"
        # 시그니처 톤: 삼겹살 주문 시 고정 멘트
        if any("삼겹" in str(it.get("name", "")) for it in items):
            return "가장 맛있는 레시피로 숙성 된 한돈을 맛있게 초벌해드릴게요!"
        parts = [f"{it['name']} {it.get('qty', 1)}개" for it in items]
        return "네, " + ", ".join(parts) + " 주문 접수했습니다. 아래 주문 내역에서 확인해 주세요."
    if intent == "call_staff":
        return "직원을 호출했습니다. 잠시만 기다려 주세요."
    if intent == "request_water":
        return "물을 준비하도록 전달했습니다."
    if intent == "request_napkin":
        return "수저·냅킨 요청을 전달했습니다."
    if intent == "request_extra_side":
        return "반찬 추가 요청을 전달했습니다."
    if intent == "cancel_order":
        return "취소 절차는 카운터에서 확인이 필요합니다. 직원 호출을 도와드릴까요?"
    if intent == "order_history":
        return "최근 주문 내역은 화면 하단 목록에서도 확인하실 수 있어요."
    if intent == "recommend":
        return "오늘은 한돈 생삼겹과 된장찌개 조합을 추천드립니다."
    if intent == "show_menu":
        return "네, 메뉴를 보여드릴게요."
    if intent == "hide_menu":
        return "네, 메뉴를 닫을게요."
    if intent == "confirm_yes":
        return "알겠습니다."
    return '제가 할 수 있는 건 주문/직원호출/물·냅킨·반찬추가예요. 예: "삼겹살 2인분 주문해줘", "직원 불러줘"'


def parse_user_text(text: str) -> IntentResult:
    raw = (text or "").strip()
    intent = detect_intent(raw)
    entities: dict[str, Any] = {"raw": raw}
    if intent == "order_menu":
        items = extract_menu_items(strip_wake_prefix(raw)) or extract_menu_items(raw)
        entities["items"] = items
    reply = build_assistant_response(intent, entities)
    return IntentResult(intent=intent, entities=entities, reply=reply)
