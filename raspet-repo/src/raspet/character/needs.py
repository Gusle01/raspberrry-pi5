"""시간 경과 요소 (다마고치 결합).

마지막 플레이 시각과 현재 시각의 차이만큼 포만도/청결도를 감소시킨다.
계획서 4.1.2 참고.
"""
from .. import config


def apply_time_decay(character, last_played_ts: float, now_ts: float) -> dict:
    """경과 시간에 비례해 돌봄 상태를 갱신한다. 변화량을 dict로 반환한다.

    Args:
        character: Character 인스턴스
        last_played_ts: 마지막 플레이 시각(epoch seconds)
        now_ts: 현재 시각(epoch seconds)
    """
    elapsed_hours = max(0.0, (now_ts - last_played_ts) / 3600.0)
    decay = int(elapsed_hours * config.NEED_DECAY_PER_HOUR)
    if decay <= 0:
        return {}

    before = {"fullness": character.fullness, "cleanliness": character.cleanliness,
              "happiness": character.happiness, "health": character.health}
    character.apply_effects({"fullness": -decay, "cleanliness": -decay})

    # 장기 방치(포만/청결이 바닥)면 행복·체력이 추가로 떨어진다.
    penalty = 0
    if character.fullness <= 0 or character.cleanliness <= 0:
        penalty = int(elapsed_hours * config.NEGLECT_HAPPINESS_PENALTY)
        if penalty > 0:
            character.apply_effects({"happiness": -penalty, "health": -penalty})

    return {
        "fullness": character.fullness - before["fullness"],
        "cleanliness": character.cleanliness - before["cleanliness"],
        "happiness": character.happiness - before["happiness"],
        "health": character.health - before["health"],
    }


def advance_day(character) -> None:
    """돌보기 행동 1회 = 하루. 하루치 자동 감소를 적용하고 일수/방치 카운터를 갱신한다.

    포만/청결이 매일 조금씩 줄어 방치 압박을 만들고, 바닥이면 행복도 함께 깎인다.
    포만·청결·행복이 연속으로 0인 일수를 세어(zero_days) 방치 엔딩 판정에 쓴다.
    """
    character.day += 1
    character.apply_effects({"fullness": -config.DAY_FULLNESS_DECAY,
                             "cleanliness": -config.DAY_CLEANLINESS_DECAY})
    if character.fullness <= 0 or character.cleanliness <= 0:
        character.apply_effects({"happiness": -config.DAY_NEGLECT_HAPPINESS})
    for need in ("fullness", "cleanliness", "happiness"):
        if getattr(character, need) <= 0:
            character.zero_days[need] = character.zero_days.get(need, 0) + 1
        else:
            character.zero_days[need] = 0


def feed(character) -> None:
    """먹이 주기: 포만도·행복도 상승."""
    character.apply_effects({"fullness": config.FEED_FULLNESS,
                             "happiness": config.FEED_HAPPINESS})


def clean(character) -> None:
    """씻기기: 청결도 상승."""
    character.apply_effects({"cleanliness": config.CLEAN_CLEANLINESS})


def play_with(character) -> None:
    """놀아주기: 행복도 상승, 스트레스 감소."""
    character.apply_effects({"happiness": config.PLAY_HAPPINESS,
                             "stress": -config.PLAY_STRESS_RELIEF})
