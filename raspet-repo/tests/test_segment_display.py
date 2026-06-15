"""4자리 7세그먼트 — 글리프 인코딩·프레임 구성·더미 폴백(하드웨어 없이 검증)."""
from raspet.hardware import segment_display as sd
from raspet.hardware.segment_display import (
    DummySegmentDisplay, create_segment_display, byte_for, text_to_frame,
)
from raspet import config


# ── 인코딩 ──────────────────────────────────────────────
def test_byte_for_known_digits():
    # SEG_ORDER 기본값(a..g,dp, MSB=a)에서 '8'은 a~g 모두 켜짐(dp 제외) = 0b11111110.
    assert byte_for("8") == 0b11111110
    assert byte_for(" ") == 0                       # 공백 = 소등
    assert byte_for("1") == byte_for("1")           # 안정적(순수 함수)
    # 알 수 없는 문자는 소등으로 폴백.
    assert byte_for("?") == 0


def test_byte_for_decimal_point_sets_dp_bit():
    dp_bit = 1 << (7 - config.SEG_ORDER.index("dp"))
    assert byte_for("8", dp=True) == byte_for("8") | dp_bit
    assert byte_for(" ", dp=True) == dp_bit


def test_text_to_frame_right_aligns_and_pads():
    frame = text_to_frame("25", 4)
    assert len(frame) == 4
    assert frame[0] == 0 and frame[1] == 0          # 왼쪽 두 자리는 공백
    assert frame[2] == byte_for("2") and frame[3] == byte_for("5")


def test_text_to_frame_decimal_does_not_consume_a_digit():
    # "2.5" 는 세 글자지만 자릿수는 2개('2'+dp, '5')만 차지한다.
    frame = text_to_frame("2.5", 4)
    assert frame[2] == byte_for("2", dp=True)
    assert frame[3] == byte_for("5")


def test_text_to_frame_truncates_overflow_keeping_rightmost():
    frame = text_to_frame("123456", 4)
    assert frame == [byte_for(c) for c in "3456"]


# ── 더미 표시(상태만 유지) ───────────────────────────────
def test_dummy_is_unavailable_but_tracks_frame():
    d = DummySegmentDisplay()
    assert d.available is False
    d.show_temp(25)
    assert d._frame == text_to_frame("25°C", d.width)
    d.show_seconds(7)
    assert d._frame == text_to_frame("7", d.width)
    d.clear()
    assert d._frame == [0] * d.width


def test_show_temp_none_clears():
    d = DummySegmentDisplay()
    d.show_seconds(9)
    d.show_temp(None)
    assert d._frame == [0] * d.width


def test_create_returns_dummy_under_dummy_flag():
    # 테스트 환경(RASPET_DUMMY=1)에서는 항상 더미.
    assert isinstance(create_segment_display(), DummySegmentDisplay)


def test_create_returns_dummy_when_disabled(monkeypatch):
    monkeypatch.setattr(config, "USE_DUMMY_HARDWARE", False)
    monkeypatch.setattr(config, "SEG_ENABLED", False)
    assert isinstance(create_segment_display(), DummySegmentDisplay)


# ── 멀티플렉싱 로직(가짜 lgpio로 하드웨어 없이 검증) ──────
class _FakeLgpio:
    """gpio_write 호출을 기록하는 lgpio 더미. 실제 핀 없이 시프트 로직만 검증한다."""
    BOTH_EDGES = 0

    def __init__(self):
        self.writes = []        # (pin, level) 기록
        self.claimed = []

    def gpiochip_open(self, n):
        return 0

    def gpiochip_close(self, h):
        pass

    def gpio_claim_output(self, h, pin, level=0):
        self.claimed.append(pin)

    def gpio_write(self, h, pin, level):
        self.writes.append((pin, level))


def test_refresh_shifts_segment_bytes_and_strobes_digits(monkeypatch):
    fake = _FakeLgpio()
    monkeypatch.setattr(sd, "lgpio", fake)
    monkeypatch.setattr(sd, "_LG_AVAILABLE", True)
    monkeypatch.setattr(config, "USE_DUMMY_HARDWARE", False)
    monkeypatch.setattr(config, "SEG_ENABLED", True)
    disp = create_segment_display()
    assert not isinstance(disp, DummySegmentDisplay)
    try:
        disp.show_text("8")                  # 오른쪽 끝 자리에 '8'
        import time
        time.sleep(0.05)                     # 갱신 스레드가 몇 사이클 돌게 둔다
        # 각 자릿수 공통핀이 한 번씩은 ON(=1)으로 켜졌는지(스트로브) 확인.
        for dpin in config.PIN_7SEG_DIGITS:
            assert (dpin, 1) in fake.writes
        # 래치핀이 토글됐는지(시프트 후 출력 반영).
        assert (config.PIN_7SEG_LATCH, 1) in fake.writes
    finally:
        disp.close()
