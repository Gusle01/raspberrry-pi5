"""도전 과제(업적) 시스템. (로드맵 6단계)

조건(능력치/재화/단계/플레이 횟수 등)을 만족하면 업적이 해금된다.
달성 목록은 캐릭터에 저장되어 영속된다. 정의는 config.ACHIEVEMENTS.
"""
from . import config


def _meets(character, requires: dict) -> bool:
    """requires의 모든 조건(속성 ≥ 값)을 만족하는지. 'stat_total'은 특수 키."""
    for key, value in requires.items():
        if key == "stat_total":
            current = character.stat_total()
        else:
            current = getattr(character, key, 0)
        if current < value:
            return False
    return True


def check_and_unlock(character) -> list[dict]:
    """아직 해금되지 않은 업적 중 조건을 만족한 것을 해금하고 새로 해금된 목록 반환."""
    newly = []
    owned = set(character.achievements)
    for ach in config.ACHIEVEMENTS:
        if ach["id"] in owned:
            continue
        if _meets(character, ach.get("requires", {})):
            character.achievements.append(ach["id"])
            newly.append(ach)
    return newly


def all_with_status(character) -> list[tuple[dict, bool]]:
    """(업적정의, 달성여부) 목록 — 업적 화면 표시용."""
    owned = set(character.achievements)
    return [(ach, ach["id"] in owned) for ach in config.ACHIEVEMENTS]
