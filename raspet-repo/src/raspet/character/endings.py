"""다중 엔딩 분기.

최종 능력치 조합을 보고 엔딩을 결정한다. (계획서 4.4 / 로드맵 5단계)
분기 조건과 문구는 config.ENDINGS 에서 관리한다.
"""
from .. import config


def determine_ending(character) -> dict:
    """캐릭터의 능력치로 엔딩을 판정한다.

    config.ENDINGS 를 순서대로 검사해, 모든 requires 조건(능력치 ≥ 값)을
    만족하는 첫 엔딩을 반환한다. 마지막의 requires 빈 항목이 기본 엔딩.
    """
    for ending in config.ENDINGS:
        requires = ending.get("requires", {})
        if all(getattr(character, stat, 0) >= value
               for stat, value in requires.items()):
            return ending
    # config가 비정상적이어도 죽지 않도록 안전망
    return {"id": "unknown", "title": "???", "desc": "이야기는 계속된다."}


def check_forced_ending(character) -> dict | None:
    """방치·스트레스로 인한 강제(나쁜) 엔딩을 판정한다. 없으면 None.

    매 하루(돌보기 행동) 후 호출한다. 스트레스가 최대치면 즉시 가출, 포만/청결/행복이
    연속 NEGLECT_ENDING_DAYS일 이상 0이면 해당 방치 엔딩을 돌려준다.
    """
    if character.stress >= config.STAT_MAX:
        return config.FORCED_ENDINGS["stress"]
    threshold = config.NEGLECT_ENDING_DAYS
    for need in ("fullness", "cleanliness", "happiness"):
        if character.zero_days.get(need, 0) >= threshold:
            return config.FORCED_ENDINGS[need]
    return None
