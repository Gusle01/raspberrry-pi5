"""4×4 매트릭스 키패드 입력.

행(row) 4개를 출력으로, 열(col) 4개를 입력(내부 풀업)으로 두고 스캔한다.
한 행만 LOW로 내리고 각 열을 읽어, LOW로 읽히는 열이 그 행에서 눌린 키다.
gpiozero/하드웨어가 없으면 더미(무입력)로 폴백한다.

pressed_edges()는 이번 호출에서 '새로' 눌린 키의 (row, col) 집합을 돌려준다(엣지 트리거).
키 라벨은 config.KEYPAD_LAYOUT에서 가져온다.
"""
from .. import config

try:
    from gpiozero import DigitalOutputDevice, DigitalInputDevice
    _GPIO_AVAILABLE = True
except Exception:
    _GPIO_AVAILABLE = False


class Keypad:
    """매트릭스 키패드. scan()으로 현재 눌린 키, pressed_edges()로 새로 눌린 키를 얻는다."""

    def __init__(self) -> None:
        self._rows = []
        self._cols = []
        self.layout = config.KEYPAD_LAYOUT
        if _GPIO_AVAILABLE and config.PIN_KEYPAD_ROWS and config.PIN_KEYPAD_COLS:
            # 행=출력(평소 HIGH), 열=입력(풀업 → 평소 HIGH, 눌리면 그 행의 LOW가 전달돼 0)
            self._rows = [DigitalOutputDevice(p, initial_value=True)
                          for p in config.PIN_KEYPAD_ROWS]
            self._cols = [DigitalInputDevice(p, pull_up=True)
                          for p in config.PIN_KEYPAD_COLS]
        self._prev: set = set()

    @property
    def available(self) -> bool:
        return bool(self._rows and self._cols)

    def scan(self) -> set:
        """지금 눌려 있는 키의 (row, col) 집합."""
        pressed = set()
        if not self.available:
            return pressed
        for r, row in enumerate(self._rows):
            row.off()                         # 이 행만 LOW
            for c, col in enumerate(self._cols):
                try:
                    if not col.value:         # 풀업이라 눌리면 0
                        pressed.add((r, c))
                except Exception:
                    pass
            row.on()                          # 다시 HIGH (다음 행 스캔 위해)
        return pressed

    def pressed_edges(self) -> set:
        """이번 호출에서 새로 눌린(직전엔 안 눌림 → 지금 눌림) 키 (row, col) 집합."""
        now = self.scan()
        edges = now - self._prev
        self._prev = now
        return edges

    def key_label(self, r: int, c: int) -> str:
        """(row, col)의 키 라벨(config.KEYPAD_LAYOUT). 범위를 벗어나면 빈 문자열."""
        try:
            return self.layout[r][c]
        except (IndexError, TypeError):
            return ""

    def close(self) -> None:
        for d in self._rows + self._cols:
            try:
                d.close()
            except Exception:
                pass
        self._rows = []
        self._cols = []


class DummyKeypad(Keypad):
    """장치가 없을 때 쓰는 무입력 키패드."""

    def __init__(self) -> None:
        self._rows = []
        self._cols = []
        self.layout = config.KEYPAD_LAYOUT
        self._prev = set()

    def scan(self) -> set:
        return set()

    def pressed_edges(self) -> set:
        return set()

    def close(self) -> None:
        pass


def create_keypad() -> Keypad:
    """가능하면 실제 키패드, 아니면 더미를 반환한다."""
    if config.USE_DUMMY_HARDWARE or not config.KEYPAD_ENABLED:
        return DummyKeypad()
    if _GPIO_AVAILABLE:
        try:
            kp = Keypad()
            if kp.available:
                return kp
            kp.close()
        except Exception:
            pass
    return DummyKeypad()
