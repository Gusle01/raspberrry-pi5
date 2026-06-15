"""4자리 7세그먼트 LED 표시 (74HC595 시프트레지스터 + 자릿수 멀티플렉싱).

평소(메뉴) 화면에서는 주변 온도를, 시간제한 미니게임에서는 남은 시간을 보여준다.

배선(요약 — 자세한 건 docs/hardware-wiring.md):
  • 74HC595 1개가 세그먼트 8선(a~g·dp)을 구동한다. Pi에서 데이터/시프트클럭/래치
    3핀(config.PIN_7SEG_DATA/CLOCK/LATCH)만 쓰면 된다.
  • 4개 자릿수 공통선은 GPIO(config.PIN_7SEG_DIGITS)로 하나씩 켠다. **공통선에는
    세그먼트 전류가 합쳐져 흐르므로 자릿수마다 트랜지스터(NPN)로 받아야 한다**
    (GPIO 직결 금지 — 과전류). 기본값은 NPN 싱크 기준(GPIO HIGH=그 자릿수 ON).
  • 한 번에 한 자릿수만 켜고 빠르게 돌려(멀티플렉싱) 사람 눈엔 4자리가 동시에 보인다.
    이 갱신은 백그라운드 스레드가 전담하므로 게임 루프 속도와 무관하다.

lgpio(또는 장치)가 없으면 다른 하드웨어 모듈처럼 더미(무동작)로 폴백한다.
"""
import threading
import time

from .. import config

try:  # Pi 5 권장 백엔드. 멀티플렉싱은 빠른 비트뱅이 필요해 lgpio로 직접 제어한다.
    import lgpio
    _LG_AVAILABLE = True
except Exception:
    _LG_AVAILABLE = False


# ── 글리프(문자 → 켜지는 세그먼트 집합) ─────────────────────
# 세그먼트 이름: a(위) b(우상) c(우하) d(아래) e(좌하) f(좌상) g(가운데).
_GLYPHS = {
    "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg",
    "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
    " ": "", "-": "g", "°": "abfg",
    "C": "adef", "F": "aefg", "H": "bcefg", "L": "def", "E": "adefg",
    "P": "abefg", "o": "cdeg", "n": "ceg", "t": "defg", "r": "eg",
}


def segments_for(ch: str) -> str:
    """문자에 해당하는 세그먼트 문자열. 모르는 문자는 공백(소등)."""
    return _GLYPHS.get(ch, "")


def byte_for(ch: str, dp: bool = False) -> int:
    """문자(+소수점)를 74HC595로 흘려보낼 8비트 값으로 인코딩한다.

    config.SEG_ORDER가 시프트 순서(처음 흘러나가는 비트가 MSB)와 세그먼트의 대응을
    정한다. 실제 배선이 다르면 SEG_ORDER만 바꾸면 코드는 그대로 둔다.
    """
    active = set(segments_for(ch))
    if dp:
        active.add("dp")
    value = 0
    for i, seg in enumerate(config.SEG_ORDER):
        if seg in active:
            value |= 1 << (7 - i)
    return value


def text_to_frame(text: str, width: int) -> list:
    """문자열을 width자리 프레임(자릿수별 8비트 값 리스트)으로 변환한다.

    '.'은 자릿수를 차지하지 않고 바로 앞 자릿수의 소수점(dp)을 켠다. 길면 오른쪽을,
    짧으면 왼쪽을 공백으로 채워 오른쪽 정렬한다.
    """
    cells = []  # (문자, dp) 목록
    for ch in str(text):
        if ch == "." and cells:
            c, _ = cells[-1]
            cells[-1] = (c, True)
        else:
            cells.append((ch, False))
    if len(cells) < width:                       # 왼쪽 공백 패딩(오른쪽 정렬)
        cells = [(" ", False)] * (width - len(cells)) + cells
    else:
        cells = cells[-width:]                    # 넘치면 오른쪽 width자리만
    return [byte_for(c, dp) for c, dp in cells]


class SegmentDisplay:
    """74HC595로 구동하는 4자리 7세그먼트. 표시 내용만 바꾸면 스레드가 계속 갱신한다."""

    def __init__(self, data, clock, latch, digit_pins,
                 digit_on=1, dwell_s=0.002) -> None:
        self._data, self._clock, self._latch = data, clock, latch
        self._digits = list(digit_pins)
        self._on = 1 if digit_on else 0
        self._off = 1 - self._on
        self._dwell = dwell_s
        self.width = len(self._digits)
        self._frame = [0] * self.width            # 자릿수별 세그먼트 값(원자적 교체)
        self._chip = lgpio.gpiochip_open(0)
        for pin in (data, clock, latch):
            lgpio.gpio_claim_output(self._chip, pin, 0)
        for pin in self._digits:                  # 처음엔 모두 소등
            lgpio.gpio_claim_output(self._chip, pin, self._off)
        self._running = True
        self._thread = threading.Thread(target=self._refresh, daemon=True)
        self._thread.start()

    @property
    def available(self) -> bool:
        return True

    # ── 표시 API (스레드 안전: 프레임 리스트를 통째로 교체) ──
    def show_text(self, text: str) -> None:
        self._frame = text_to_frame(text, self.width)

    def show_int(self, n: int) -> None:
        self.show_text(str(int(n)))

    def show_seconds(self, seconds) -> None:
        """남은 시간(초)을 정수로 오른쪽 정렬해 표시한다."""
        self.show_text(str(max(0, int(seconds))))

    def show_temp(self, celsius) -> None:
        """주변 온도를 'NN°C' 형태로 표시한다. None이면 소등."""
        if celsius is None:
            self.clear()
        else:
            self.show_text(f"{round(celsius)}°C")

    def clear(self) -> None:
        self._frame = [0] * self.width

    # ── 멀티플렉싱 갱신 루프(백그라운드) ──────────────────
    def _refresh(self) -> None:
        while self._running:
            frame = self._frame                   # 스냅샷(다른 스레드가 교체해도 안전)
            for i, dpin in enumerate(self._digits):
                try:
                    self._shift_out(frame[i])
                    lgpio.gpio_write(self._chip, dpin, self._on)
                    time.sleep(self._dwell)
                    lgpio.gpio_write(self._chip, dpin, self._off)
                except Exception:
                    return                        # 장치 오류 시 조용히 멈춘다

    def _shift_out(self, value: int) -> None:
        c, d, clk, lat = self._chip, self._data, self._clock, self._latch
        for b in range(8):                        # MSB부터 흘려보낸다
            lgpio.gpio_write(c, d, (value >> (7 - b)) & 1)
            lgpio.gpio_write(c, clk, 1)
            lgpio.gpio_write(c, clk, 0)
        lgpio.gpio_write(c, lat, 1)               # 래치 → 출력 반영
        lgpio.gpio_write(c, lat, 0)

    def close(self) -> None:
        self._running = False
        if self._thread.is_alive():
            self._thread.join(timeout=0.5)
        try:
            for pin in self._digits:              # 종료 시 모두 소등
                lgpio.gpio_write(self._chip, pin, self._off)
            lgpio.gpiochip_close(self._chip)
        except Exception:
            pass


class DummySegmentDisplay(SegmentDisplay):
    """장치가 없을 때 쓰는 무동작 표시(모든 메서드 no-op)."""

    def __init__(self) -> None:
        self.width = len(config.PIN_7SEG_DIGITS)
        self._frame = [0] * self.width

    @property
    def available(self) -> bool:
        return False

    def show_text(self, text: str) -> None:
        self._frame = text_to_frame(text, self.width)   # 상태만 유지(테스트용)

    def clear(self) -> None:
        self._frame = [0] * self.width

    def close(self) -> None:
        pass


def create_segment_display() -> SegmentDisplay:
    """가능하면 실제 7세그먼트, 아니면 더미를 반환한다."""
    if config.USE_DUMMY_HARDWARE or not config.SEG_ENABLED:
        return DummySegmentDisplay()
    if _LG_AVAILABLE:
        try:
            return SegmentDisplay(
                config.PIN_7SEG_DATA, config.PIN_7SEG_CLOCK, config.PIN_7SEG_LATCH,
                config.PIN_7SEG_DIGITS, digit_on=config.SEG_DIGIT_ON_LEVEL,
                dwell_s=config.SEG_DWELL_S,
            )
        except Exception:
            pass
    return DummySegmentDisplay()
