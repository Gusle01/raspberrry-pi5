"""랜덤 이벤트 시스템. (로드맵 6단계)

미니게임 후 또는 '탐험' 시 확률적으로 사건이 발생해 캐릭터 상태가 변한다.
이벤트 정의(제목·설명·가중치·효과)는 config.EVENTS 에서 관리한다.
"""
import random

from . import config


def pick_event(rng: random.Random, character=None) -> dict | None:
    """가중치에 따라 이벤트 하나를 고른다(적용은 하지 않음)."""
    pool = config.EVENTS
    if not pool:
        return None
    weights = [max(1, e.get("weight", 1)) for e in pool]
    return rng.choices(pool, weights=weights, k=1)[0]


def apply_event(event: dict, character) -> None:
    """이벤트 효과를 캐릭터에 적용한다."""
    effect = event.get("effect")
    if effect:
        character.apply_effects(effect)


def force_event(character, rng: random.Random) -> dict | None:
    """반드시 이벤트를 하나 발생시키고 그 정의를 반환한다('탐험'용)."""
    event = pick_event(rng, character)
    if event:
        apply_event(event, character)
    return event


def maybe_trigger(character, rng: random.Random) -> dict | None:
    """EVENT_CHANCE 확률로 이벤트를 발생시킨다. 발생하면 정의를, 아니면 None."""
    if rng.random() >= config.EVENT_CHANCE:
        return None
    return force_event(character, rng)
