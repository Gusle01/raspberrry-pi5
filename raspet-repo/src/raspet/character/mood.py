"""감정 표현 — 캐릭터 상태로부터 현재 무드를 계산한다. (로드맵 6단계)

무드는 화면의 표정 렌더링과 인사말에 쓰인다. 임계값은 config에서 가져온다.
"""
from .. import config

# 무드 id → 한국어 라벨
MOOD_LABELS = {
    "sick": "아파요",
    "hungry": "배고파요",
    "dirty": "지저분해요",
    "stressed": "짜증나요",
    "happy": "행복해요",
    "sad": "우울해요",
    "neutral": "그저그래요",
}


def compute_mood(character) -> str:
    """캐릭터 상태를 보고 무드 id를 반환한다(우선순위: 위에서 아래로)."""
    if character.health <= config.MOOD_HEALTH_SICK:
        return "sick"
    if character.fullness <= config.MOOD_FULLNESS_HUNGRY:
        return "hungry"
    if character.cleanliness <= config.MOOD_CLEAN_DIRTY:
        return "dirty"
    if character.stress >= config.MOOD_STRESS_HIGH:
        return "stressed"
    if character.happiness >= config.MOOD_HAPPY:
        return "happy"
    if character.happiness <= config.MOOD_SAD:
        return "sad"
    return "neutral"


def mood_label(character) -> str:
    return MOOD_LABELS.get(compute_mood(character), "")
