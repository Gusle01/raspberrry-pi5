"""XP/레벨 진행도 — 누적 XP를 레벨·타이틀·진행도로 변환한다.

기존 세부 능력치·진화(stage)와 독립된 "전체 진행도" 레이어다.
레벨 임계값은 config의 XP_LEVEL_* 상수로 계산하므로, 곡선을 바꾸려면
그 수치만 고치면 된다(코드에 임계값을 박지 않는다).
"""
from .. import config


def xp_for_level(level: int) -> int:
    """`level`이 되기 위해 필요한 누적 XP. Lv.1 = 0.

    레벨 L→L+1 비용 = XP_LEVEL_BASE + (L-1)*XP_LEVEL_STEP 를 누적한 값.
    """
    level = max(1, min(int(level), config.XP_MAX_LEVEL))
    total = 0
    for k in range(1, level):
        total += config.XP_LEVEL_BASE + (k - 1) * config.XP_LEVEL_STEP
    return total


def level_for_xp(xp: int) -> int:
    """누적 XP에 해당하는 레벨(1 ~ XP_MAX_LEVEL)."""
    level = 1
    while level < config.XP_MAX_LEVEL and xp >= xp_for_level(level + 1):
        level += 1
    return level


def title_for_level(level: int) -> str:
    """레벨 이하에서 가장 높은 마일스톤 타이틀(없으면 빈 문자열)."""
    title = ""
    for lv in sorted(config.LEVEL_TITLES):
        if lv <= level:
            title = config.LEVEL_TITLES[lv]
    return title


def progress(xp: int) -> tuple[int, int, float]:
    """현재 레벨 구간의 (채운 XP, 필요 XP, 진행비율 0.0~1.0).

    최대 레벨에 도달하면 (0, 0, 1.0)을 반환한다.
    """
    level = level_for_xp(xp)
    if level >= config.XP_MAX_LEVEL:
        return 0, 0, 1.0
    base = xp_for_level(level)
    need = xp_for_level(level + 1) - base
    into = xp - base
    ratio = into / need if need else 1.0
    return into, need, max(0.0, min(1.0, ratio))
