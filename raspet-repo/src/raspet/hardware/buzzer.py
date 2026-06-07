"""피에조 부저 (효과음 피드백, 선택)."""
from .. import config


class Buzzer:
    """간단한 효과음 출력."""

    def __init__(self) -> None:
        # TODO: gpiozero.TonalBuzzer 또는 PWM 초기화
        pass

    def beep(self, freq: int = 880, duration: float = 0.1) -> None:
        # TODO: 지정 주파수로 소리 출력
        pass
