"""환경 센서 — 조도(LDR) + 온도/기압(BMP180). (로드맵 확장)

게임에 두 가지 환경 입력을 제공한다.
  • 조도센서(LDR + MCP3008 ADC): 밝으면 낮(펫이 깸), 어두우면 밤(펫이 잠).
  • BMP180(I2C): 주변 온도(℃)와 기압(hPa). 온도로 더위/추위를 표현한다.

※ BMP180은 **습도 측정 기능이 없다**(온도+기압만). 습도까지 쓰려면 BME280 등
  습도 지원 센서로 교체하면 된다. 이 모듈은 그때 humidity()가 실제 값을 돌려주도록
  자리를 비워둔다(현재는 항상 None).

라이브러리/장치가 없으면 다른 하드웨어 모듈과 동일하게 더미(중립)로 폴백하므로
PC·미연결 상태에서도 임포트·실행이 깨지지 않는다.
"""
import time

from .. import config

try:  # 조도센서(LDR)는 조이스틱과 같은 MCP3008(SPI)을 쓴다.
    from gpiozero import MCP3008
    _ADC_AVAILABLE = True
except Exception:
    _ADC_AVAILABLE = False

try:  # BMP180은 I2C. smbus2(권장) → smbus 순으로 시도한다.
    from smbus2 import SMBus
    _I2C_AVAILABLE = True
except Exception:
    try:
        from smbus import SMBus
        _I2C_AVAILABLE = True
    except Exception:
        _I2C_AVAILABLE = False


class EnvReading:
    """한 시점의 환경 측정 스냅샷(매 프레임 I2C를 다시 읽지 않도록 캐싱용).

    값이 없으면(센서 미연결) 해당 항목은 None이다.
    """

    __slots__ = ("light", "temperature_c", "pressure_hpa", "humidity")

    def __init__(self, light=None, temperature_c=None,
                 pressure_hpa=None, humidity=None) -> None:
        self.light = light                # 0.0(캄캄) ~ 1.0(매우 밝음) 또는 None
        self.temperature_c = temperature_c
        self.pressure_hpa = pressure_hpa
        self.humidity = humidity          # 현재 BMP180엔 없음 → 항상 None

    def is_dark(self, below: float | None = None) -> bool:
        """조도값이 임계값 이하이면 어둡다고 본다. 값이 없으면 False."""
        if self.light is None:
            return False
        thr = config.LIGHT_DARK_BELOW if below is None else below
        return self.light <= thr

    def mood_signals(self) -> dict:
        """compute_mood에 넘길 환경 신호 묶음(온도/수면/조도)."""
        return {
            "temperature_c": self.temperature_c,
            "humidity": self.humidity,
            "light": self.light,
            "asleep": self.is_dark(),
        }


class _BMP180:
    """BMP180 온도·기압 센서 드라이버 (smbus 기반, 외부 의존성 없음).

    데이터시트의 보정 계수/공식을 그대로 구현한다. 읽기 실패 시 예외를 던지므로
    호출부에서 안전하게 폴백한다.
    """

    _REG_CONTROL = 0xF4
    _REG_RESULT = 0xF6
    _CMD_TEMP = 0x2E
    _CMD_PRESSURE = 0x34

    def __init__(self, bus_num: int, addr: int, oss: int = 1) -> None:
        self._bus = SMBus(bus_num)
        self._addr = addr
        self._oss = max(0, min(3, oss))
        self._cal = self._read_calibration()

    # ── 저수준 I2C ──────────────────────────────────────
    def _read_s16(self, reg: int) -> int:
        hi, lo = self._bus.read_i2c_block_data(self._addr, reg, 2)
        val = (hi << 8) + lo
        return val - 65536 if val > 32767 else val

    def _read_u16(self, reg: int) -> int:
        hi, lo = self._bus.read_i2c_block_data(self._addr, reg, 2)
        return (hi << 8) + lo

    def _read_calibration(self) -> dict:
        return {
            "AC1": self._read_s16(0xAA), "AC2": self._read_s16(0xAC),
            "AC3": self._read_s16(0xAE), "AC4": self._read_u16(0xB0),
            "AC5": self._read_u16(0xB2), "AC6": self._read_u16(0xB4),
            "B1": self._read_s16(0xB6), "B2": self._read_s16(0xB8),
            "MB": self._read_s16(0xBA), "MC": self._read_s16(0xBC),
            "MD": self._read_s16(0xBE),
        }

    def _read_raw_temp(self) -> int:
        self._bus.write_byte_data(self._addr, self._REG_CONTROL, self._CMD_TEMP)
        time.sleep(0.005)
        return self._read_u16(self._REG_RESULT)

    def _read_raw_pressure(self) -> int:
        cmd = self._CMD_PRESSURE + (self._oss << 6)
        self._bus.write_byte_data(self._addr, self._REG_CONTROL, cmd)
        time.sleep(0.005 + 0.003 * self._oss)
        hi, lo, xlo = self._bus.read_i2c_block_data(self._addr, self._REG_RESULT, 3)
        return ((hi << 16) + (lo << 8) + xlo) >> (8 - self._oss)

    def _b5(self, ut: int) -> int:
        c = self._cal
        x1 = ((ut - c["AC6"]) * c["AC5"]) >> 15
        x2 = (c["MC"] << 11) // (x1 + c["MD"])
        return x1 + x2

    def read(self) -> tuple[float, float]:
        """(온도℃, 기압hPa)를 반환한다."""
        c = self._cal
        ut = self._read_raw_temp()
        b5 = self._b5(ut)
        temp_c = ((b5 + 8) >> 4) / 10.0

        up = self._read_raw_pressure()
        oss = self._oss
        b6 = b5 - 4000
        x1 = (c["B2"] * ((b6 * b6) >> 12)) >> 11
        x2 = (c["AC2"] * b6) >> 11
        x3 = x1 + x2
        b3 = (((c["AC1"] * 4 + x3) << oss) + 2) >> 2
        x1 = (c["AC3"] * b6) >> 13
        x2 = (c["B1"] * ((b6 * b6) >> 12)) >> 16
        x3 = ((x1 + x2) + 2) >> 2
        b4 = (c["AC4"] * (x3 + 32768)) >> 15
        b7 = (up - b3) * (50000 >> oss)
        p = (b7 * 2) // b4 if b7 < 0x80000000 else (b7 // b4) * 2
        x1 = (p >> 8) * (p >> 8)
        x1 = (x1 * 3038) >> 16
        x2 = (-7357 * p) >> 16
        p = p + ((x1 + x2 + 3791) >> 4)
        return temp_c, p / 100.0


class Environment:
    """조도 + 온도/기압 센서 묶음. 어느 한쪽만 연결돼도 동작한다."""

    def __init__(self) -> None:
        self._ldr = None
        self._bmp = None
        if _ADC_AVAILABLE:
            try:
                self._ldr = MCP3008(channel=config.ADC_CHANNEL_LIGHT)
            except Exception:
                self._ldr = None
        if _I2C_AVAILABLE:
            try:
                self._bmp = _BMP180(config.BMP180_I2C_BUS, config.BMP180_I2C_ADDR,
                                    oss=config.BMP180_OVERSAMPLING)
            except Exception:
                self._bmp = None

    @property
    def available(self) -> bool:
        return self._ldr is not None or self._bmp is not None

    @property
    def light_available(self) -> bool:
        return self._ldr is not None

    @property
    def temp_available(self) -> bool:
        return self._bmp is not None

    def light(self):
        """조도 0.0(캄캄)~1.0(밝음). 센서 없으면 None."""
        if self._ldr is None:
            return None
        v = float(self._ldr.value)
        return 1.0 - v if config.LIGHT_INVERT else v

    def read(self) -> EnvReading:
        """현재 환경을 한 번에 읽어 스냅샷으로 반환한다."""
        light = self.light()
        temp = pressure = None
        if self._bmp is not None:
            try:
                temp, pressure = self._bmp.read()
            except Exception:
                temp = pressure = None
        # 습도: BMP180은 미지원 → 항상 None. (BME280 등으로 교체 시 여기서 채운다.)
        return EnvReading(light=light, temperature_c=temp,
                          pressure_hpa=pressure, humidity=None)


class DummyEnvironment(Environment):
    """센서가 없을 때 쓰는 더미 — 모든 값이 None(중립)."""

    def __init__(self) -> None:
        self._ldr = None
        self._bmp = None

    def read(self) -> EnvReading:
        return EnvReading()


def create_environment() -> Environment:
    """가능하면 실제 센서, 아니면 더미를 반환한다."""
    if config.USE_DUMMY_HARDWARE:
        return DummyEnvironment()
    env = Environment()
    return env if env.available else DummyEnvironment()
