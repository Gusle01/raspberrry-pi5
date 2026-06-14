"""피에조 부저 (효과음 피드백, 선택).

하드웨어가 없으면 더미(no-op) 구현으로 폴백한다.
"""
from .. import config

try:
    from gpiozero import TonalBuzzer
    from gpiozero.tones import Tone
    _GPIO_AVAILABLE = True
except Exception:
    _GPIO_AVAILABLE = False


class Buzzer:
    """간단한 효과음 출력."""

    def __init__(self) -> None:
        self._buzzer = None
        if _GPIO_AVAILABLE and config.PIN_BUZZER is not None:
            self._buzzer = TonalBuzzer(config.PIN_BUZZER)

    @property
    def available(self) -> bool:
        return self._buzzer is not None

    def beep(self, freq: int = 880, duration: float = 0.1) -> None:
        """지정 주파수로 잠깐 소리를 낸다."""
        if self._buzzer is None:
            return
        import time
        self._buzzer.play(Tone(frequency=freq))
        time.sleep(duration)
        self._buzzer.stop()


class DummyBuzzer(Buzzer):
    """장치가 없을 때 사용하는 무음 부저."""

    def __init__(self) -> None:
        self._buzzer = None


def create_buzzer() -> Buzzer:
    """가능하면 실제 부저, 아니면 더미를 반환한다."""
    if config.USE_DUMMY_HARDWARE:
        return DummyBuzzer()
    if _GPIO_AVAILABLE and config.PIN_BUZZER is not None:
        try:
            return Buzzer()
        except Exception:
            pass
    return DummyBuzzer()
