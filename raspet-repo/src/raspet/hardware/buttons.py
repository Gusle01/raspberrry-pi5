"""푸시 버튼 입력 (두더지 잡기 등).

눌린 '순간'(엣지)만 보고한다. 하드웨어가 없으면 더미로 폴백한다.
config.PIN_BUTTONS의 핀 순서가 버튼 인덱스 0·1·2(왼·가운데·오른쪽)에 대응한다.
"""
from .. import config

try:
    from gpiozero import Button
    _GPIO_AVAILABLE = True
except Exception:
    _GPIO_AVAILABLE = False


class Buttons:
    """GPIO 버튼 묶음. pressed_edges()로 이번에 새로 눌린 버튼 집합을 얻는다."""

    def __init__(self) -> None:
        self._btns = []
        if _GPIO_AVAILABLE and config.PIN_BUTTONS:
            # 버튼 → GND 배선 + 내부 풀업(평소 HIGH, 누르면 LOW)
            self._btns = [Button(pin, pull_up=True) for pin in config.PIN_BUTTONS]
        self.count = len(config.PIN_BUTTONS)
        self._prev = [False] * len(self._btns)

    @property
    def available(self) -> bool:
        return bool(self._btns)

    def pressed_edges(self) -> set:
        """이번 호출에서 새로 눌린(이전엔 안 눌림 → 지금 눌림) 버튼 인덱스 집합."""
        out = set()
        for i, b in enumerate(self._btns):
            try:
                now = bool(b.is_pressed)
            except Exception:
                now = False
            if now and not self._prev[i]:
                out.add(i)
            self._prev[i] = now
        return out

    def close(self) -> None:
        for b in self._btns:
            try:
                b.close()
            except Exception:
                pass
        self._btns = []


class DummyButtons(Buttons):
    """장치가 없을 때 쓰는 무입력 버튼."""

    def __init__(self) -> None:
        self._btns = []
        self.count = len(config.PIN_BUTTONS)
        self._prev = []

    def pressed_edges(self) -> set:
        return set()

    def close(self) -> None:
        pass


def create_buttons() -> Buttons:
    """가능하면 실제 버튼, 아니면 더미를 반환한다."""
    if config.USE_DUMMY_HARDWARE:
        return DummyButtons()
    if _GPIO_AVAILABLE and config.PIN_BUTTONS:
        try:
            return Buttons()
        except Exception:
            pass
    return DummyButtons()
