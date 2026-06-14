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
            # 효과음이 392~1047Hz를 쓴다. 기본(1옥타브, 약 220~880Hz)으론 좁아
            # 범위를 벗어난 음에서 ValueError가 나므로 2옥타브(약 110~1760Hz)로 잡는다.
            self._buzzer = TonalBuzzer(config.PIN_BUZZER, octaves=2)

    @property
    def available(self) -> bool:
        return self._buzzer is not None

    def beep(self, freq: int = 880, duration: float = 0.1) -> None:
        """지정 주파수로 잠깐 소리를 낸다.

        효과음은 부가 요소이므로, 범위를 벗어나거나 장치 오류가 나더라도
        게임이 멈추지 않게 주파수를 지원 범위로 보정하고 예외를 삼킨다.
        """
        if self._buzzer is None:
            return
        import time
        try:
            lo = self._buzzer.min_tone.frequency
            hi = self._buzzer.max_tone.frequency
            freq = max(lo, min(hi, freq))     # 장치 지원 범위로 클램프
            self._buzzer.play(Tone(frequency=freq))
            time.sleep(duration)
            self._buzzer.stop()
        except Exception:                     # 효과음 실패가 게임을 멈추게 하지 않는다
            try:
                self._buzzer.stop()
            except Exception:
                pass


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
