"""시간 경과 요소 (다마고치 결합).

마지막 플레이 시각과 현재 시각의 차이만큼 포만도/청결도를 감소시킨다.
계획서 4.1.2 참고.
"""
from .. import config


def apply_time_decay(character, last_played_ts: float, now_ts: float) -> None:
    """경과 시간(초)에 비례해 돌봄 상태를 갱신한다.

    Args:
        character: Character 인스턴스
        last_played_ts: 마지막 플레이 시각(epoch seconds)
        now_ts: 현재 시각(epoch seconds)
    """
    elapsed_hours = max(0.0, (now_ts - last_played_ts) / 3600.0)
    decay = int(elapsed_hours * config.NEED_DECAY_PER_HOUR)
    # TODO: fullness/cleanliness 감소, 장기 방치 시 happiness/health 하락
    raise NotImplementedError
