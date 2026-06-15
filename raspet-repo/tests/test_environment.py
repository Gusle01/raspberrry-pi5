"""환경 센서(조도 + 온도) 통합 테스트.

- 조도 기반 낮/밤 판정(조도센서 우선, 시계 폴백)
- 온도/수면 기반 무드(더위/추위/잠) — 센서 미연결 시 영향 없음
- EnvReading 동작과 더미 폴백
"""
from datetime import datetime

from raspet.character.character import Character
from raspet.character import mood
from raspet.core import daytime
from raspet.hardware.environment import (
    EnvReading, Environment, DummyEnvironment, create_environment, _DHT11,
)
from raspet import config


def _ch(**kw) -> Character:
    """건강한 기본값(다른 무드 규칙이 오발되지 않도록)."""
    base = dict(health=80, fullness=80, cleanliness=80, stress=10, happiness=50)
    base.update(kw)
    return Character(**base)


class _FakeEnv:
    """light_available 과 read()만 흉내내는 조도센서 스텁."""

    def __init__(self, light) -> None:
        self.light_available = light is not None
        self._light = light

    def read(self) -> EnvReading:
        return EnvReading(light=self._light)


# ── EnvReading ───────────────────────────────────────────
def test_env_reading_defaults_are_none():
    r = EnvReading()
    assert r.light is None and r.temperature_c is None
    assert r.humidity is None            # 센서 미연결 → 기본값은 모두 None
    assert r.is_dark() is False          # 값이 없으면 어둡다고 보지 않음


def test_is_dark_uses_threshold():
    assert EnvReading(light=0.1).is_dark() is True
    assert EnvReading(light=0.9).is_dark() is False
    assert EnvReading(light=config.LIGHT_DARK_BELOW).is_dark() is True   # 경계 포함(<=)


def test_mood_signals_shape():
    sig = EnvReading(light=0.8, temperature_c=22.0).mood_signals()
    assert set(sig) == {"temperature_c", "humidity", "light", "asleep"}
    assert sig["asleep"] is False        # 밝으면 안 잔다


# ── 조도 우선 낮/밤 판정 ─────────────────────────────────
_NOON = datetime(2026, 6, 15, 13, 0)     # 시계상 '낮'
_MIDNIGHT = datetime(2026, 6, 15, 2, 0)  # 시계상 '밤'


def test_dark_forces_night_even_at_noon():
    assert daytime.current_period(now=_NOON, env=_FakeEnv(0.05)) == "night"


def test_bright_keeps_clock_period():
    assert daytime.current_period(now=_NOON, env=_FakeEnv(0.9)) == "day"


def test_bright_at_clock_night_is_awake_day():
    # 밤이지만 불을 켜 밝으면 → 깨어있는 것으로 보고 'day'
    assert daytime.current_period(now=_MIDNIGHT, env=_FakeEnv(0.9)) == "day"


def test_no_light_sensor_falls_back_to_clock():
    assert daytime.current_period(now=_MIDNIGHT, env=_FakeEnv(None)) == "night"
    assert daytime.current_period(now=_NOON, env=None) == "day"


# ── 온도/수면 무드 (env 신호) ────────────────────────────
def _m(ch, **env):
    return mood.compute_mood(ch, period="day", env=env)


def test_hot_when_warm():
    assert _m(_ch(), temperature_c=config.TEMP_HOT_ABOVE_C, asleep=False) == "hot"


def test_cold_when_chilly():
    assert _m(_ch(), temperature_c=config.TEMP_COLD_BELOW_C, asleep=False) == "cold"


def test_comfortable_temp_is_neutral():
    assert _m(_ch(), temperature_c=22.0, asleep=False) == "neutral"


def test_humid_when_sticky():
    assert _m(_ch(), humidity=config.HUMID_HIGH_ABOVE, asleep=False) == "humid"


def test_missing_humidity_does_not_trigger_humid():
    assert _m(_ch(), humidity=None, asleep=False) == "neutral"
    assert _m(_ch(), humidity=40, asleep=False) == "neutral"


# ── DHT11 디코더 (하드웨어 없이 비트 디코딩만 검증) ──────────
def _dht_frame(humidity: int, temp: int):
    """DHT11 한 프레임을 (levels, counts)로 합성한다(체크섬 포함).

    각 비트는 50µs LOW + HIGH(짧으면 0·길면 1)로 표현된다. 절대 길이 대신
    상대 길이만 의미가 있으므로 count는 작은 정수로 흉내낸다.
    """
    data = [humidity, 0, temp, 0]
    data.append(sum(data) & 0xFF)
    levels, counts = [1], [3]                 # 센서 응답 HIGH(핸드셰이크)
    for byte in data:
        for i in range(8):
            bit = (byte >> (7 - i)) & 1
            levels += [0, 1]
            counts += [2, 6 if bit else 2]    # LOW, HIGH(1이면 길게)
    return levels, counts


def test_dht11_decode_roundtrip():
    temp, hum = _DHT11._decode(*_dht_frame(humidity=55, temp=23))
    assert (temp, hum) == (23.0, 55.0)


def test_dht11_decode_rejects_bad_checksum():
    levels, counts = _dht_frame(humidity=55, temp=23)
    counts[-1] = 6 if counts[-1] == 2 else 2   # 마지막 비트(체크섬) 한 개 뒤집기
    try:
        _DHT11._decode(levels, counts)
        assert False, "체크섬 오류를 잡지 못했다"
    except RuntimeError:
        pass


def test_missing_temperature_does_not_trigger_hot_cold():
    # 온도 센서 미연결(None) → 더위/추위 규칙은 매칭되지 않는다.
    assert _m(_ch(), temperature_c=None, asleep=False) == "neutral"
    assert mood.compute_mood(_ch(), period="day", env=None) == "neutral"


def test_asleep_when_dark():
    assert _m(_ch(), asleep=True) == "asleep"


def test_asleep_outranks_temperature_but_not_sickness():
    # 어두우면 더워도 잠든 모습이 우선
    assert _m(_ch(), temperature_c=35.0, asleep=True) == "asleep"
    # 하지만 아픈 상태는 잠보다 우선(돌봐야 함)
    assert _m(_ch(health=10), asleep=True) == "sick"


# ── 더미 폴백 ────────────────────────────────────────────
def test_dummy_environment_is_neutral():
    env = DummyEnvironment()
    assert env.available is False
    assert env.light_available is False
    r = env.read()
    assert r.light is None and r.temperature_c is None


def test_create_environment_dummy_under_flag():
    # 테스트 환경(RASPET_DUMMY=1)에서는 항상 더미가 나온다.
    assert isinstance(create_environment(), Environment)
