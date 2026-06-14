"""감정 표현 — 캐릭터 상태로부터 현재 무드를 계산한다. (로드맵 6단계)

무드는 화면의 표정 렌더링과 인사말에 쓰인다. 표정 집합과 상태→표정 매핑은
config.MOODS(데이터)로 정의하며, 이 모듈은 그 규칙을 우선순위 순으로 평가만 한다.
"""
import operator

from .. import config

# 무드 id → 한국어 라벨 (config 데이터에서 파생 + 이벤트 전용 라벨 병합)
MOOD_LABELS = {m["id"]: m["label"] for m in config.MOODS}
MOOD_LABELS.update(config.MOOD_LABELS_EXTRA)

_OPS = {
    "<=": operator.le, ">=": operator.ge, "==": operator.eq,
    "<": operator.lt, ">": operator.gt,
}


def _current_period() -> str:
    """현재 시간대('morning'/'day'/'evening'/'night'). 지연 import로 순환참조 회피."""
    from ..core import daytime
    return daytime.current_period()


def _signal(character, period, name):
    if name == "period":
        return period
    return getattr(character, name)


def compute_mood(character, period: str | None = None) -> str:
    """캐릭터 상태를 보고 무드 id를 반환한다.

    config.MOODS를 위에서부터 검사해 모든 조건(AND)을 만족하는 첫 규칙을 채택한다.
    마지막 규칙(neutral)은 빈 조건이라 항상 매칭되므로 기본값 역할을 한다.

    Args:
        character: Character 인스턴스
        period: 시간대 문자열. 생략하면 현재 시각으로 계산한다(졸림 판정용).
    """
    if period is None:
        period = _current_period()
    for rule in config.MOODS:
        if all(_OPS[op](_signal(character, period, sig), val)
               for sig, op, val in rule["when"]):
            return rule["id"]
    return "neutral"


def mood_label(character, period: str | None = None) -> str:
    return MOOD_LABELS.get(compute_mood(character, period), "")
