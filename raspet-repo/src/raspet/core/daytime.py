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


def current_period(now: datetime | None = None, env=None) -> str:
    """현재 시간대를 반환한다.

    조도센서(env)가 있으면 그것을 우선한다(요청: 밝으면 낮/깸, 어두우면 밤/잠):
      • 어두움  → 'night'  (펫이 잠든다)
      • 밝음    → 시계 기반(morning/day/evening) — 단 시계가 밤이어도 밝으면 'day'로 본다.
    조도센서가 없으면(env=None 또는 미연결) 기존처럼 시스템 시계로만 판정한다.

    Args:
        now: 기준 시각(테스트 주입용). 생략 시 현재 시각.
        env: 조도센서를 가진 환경 객체(hardware.environment.Environment). 선택.
    """
    now = now or datetime.now()
    clock = period_for_hour(now.hour)
    if env is not None and getattr(env, "light_available", False):
        if env.read().is_dark():
            return "night"
        return clock if clock != "night" else "day"   # 밝은데 시계만 밤 → 깨어있음(day)
    return clock


def tint(period: str) -> tuple:
    """시간대별 배경 색조."""
    return config.DAYTIME_TINT.get(period, config.COLOR_BG)


def greeting(period: str) -> str:
    return GREETINGS.get(period, "")
