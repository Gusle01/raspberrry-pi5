"""시간대 반영 — 현재 시각을 아침/낮/저녁/밤으로 구분한다. (로드맵 6단계)

배경 색조와 인사말에 쓰인다. 경계값/색은 config에서 가져온다.
시간(hour)은 주입 가능하게 하여 테스트할 수 있다.
"""
from datetime import datetime

from .. import config

GREETINGS = {
    "morning": "좋은 아침이에요!",
    "day": "활기찬 한낮이에요.",
    "evening": "노을이 지고 있어요.",
    "night": "별이 빛나는 밤이에요.",
}


def period_for_hour(hour: int) -> str:
    """0~23시 → 'morning'/'day'/'evening'/'night'."""
    for name, (start, end) in config.DAYTIME_BOUNDS.items():
        if start <= hour < end:
            return name
    return "night"


def current_period(now: datetime | None = None) -> str:
    now = now or datetime.now()
    return period_for_hour(now.hour)


def tint(period: str) -> tuple:
    """시간대별 배경 색조."""
    return config.DAYTIME_TINT.get(period, config.COLOR_BG)


def greeting(period: str) -> str:
    return GREETINGS.get(period, "")
