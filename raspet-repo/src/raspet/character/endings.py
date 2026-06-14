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
