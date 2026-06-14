"""LED 출력 (두더지 잡기 등의 시각 피드백).

하드웨어가 없으면 더미(no-op) 구현으로 폴백한다. config.PIN_LEDS의 핀 순서가
구멍 인덱스 0·1·2(왼·가운데·오른쪽)에 대응한다.
"""
from .. import config

try:
    from gpiozero import LED
    _GPIO_AVAILABLE = True
except Exception:
    _GPIO_AVAILABLE = False


class Leds:
    """GPIO LED 묶음. set(i, on)으로 개별 점등/소등한다."""

    def __init__(self) -> None:
        self._leds = []
        if _GPIO_AVAILABLE and config.PIN_LEDS:
            self._leds = [LED(pin) for pin in config.PIN_LEDS]
        self.count = len(config.PIN_LEDS)

    @property
    def available(self) -> bool:
        return bool(self._leds)

    def set(self, index: int, on: bool) -> None:
        """index번 LED를 켜거나 끈다(범위 밖/오류는 조용히 무시)."""
        if not (0 <= index < len(self._leds)):
            return
        try:
            self._leds[index].on() if on else self._leds[index].off()
        except Exception:                 # LED 실패가 게임을 멈추게 하지 않는다
            pass

    def all_off(self) -> None:
        for i in range(len(self._leds)):
            self.set(i, False)

    def close(self) -> None:
        for led in self._leds:
            try:
                led.close()
            except Exception:
                pass
        self._leds = []


class DummyLeds(Leds):
    """장치가 없을 때 쓰는 무동작 LED (인덱스/개수는 그대로 노출)."""

    def __init__(self) -> None:
        self._leds = []
        self.count = len(config.PIN_LEDS)

    def set(self, index: int, on: bool) -> None:
        pass

    def close(self) -> None:
        pass


def create_leds() -> Leds:
    """가능하면 실제 LED, 아니면 더미를 반환한다."""
    if config.USE_DUMMY_HARDWARE:
        return DummyLeds()
    if _GPIO_AVAILABLE and config.PIN_LEDS:
        try:
            return Leds()
        except Exception:
            pass
    return DummyLeds()
