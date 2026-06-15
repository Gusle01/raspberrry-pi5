"""환경 센서 — 조도(LDR) + 온도/습도(DHT11). (로드맵 확장)

게임에 두 가지 환경 입력을 제공한다.
  • 조도센서(LDR + MCP3008 ADC): 밝으면 낮(펫이 깸), 어두우면 밤(펫이 잠).
  • DHT11(단선 디지털): 주변 온도(℃)와 습도(%). 온도로 더위/추위를, 습도로 끈적함을 표현한다.

※ DHT11은 단선(1-wire 방식) 디지털 센서라 I2C가 아니라 GPIO 1개를 쓴다. 기압은 못
  재지만 습도를 잰다(정밀도 낮음: 온도 ±2℃·습도 ±5%, 정수 단위). 더 정밀하게 쓰려면
  DHT22/BME280 등으로 교체하고 _DHT11.read()가 돌려주는 값만 맞춰주면 된다.

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

try:  # DHT11은 단선 디지털. Pi 5 권장 백엔드인 lgpio로 핀을 직접 제어한다.
    import lgpio
    _DHT_AVAILABLE = True
except Exception:
    _DHT_AVAILABLE = False


class EnvReading:
    """한 시점의 환경 측정 스냅샷(매 프레임 I2C를 다시 읽지 않도록 캐싱용).

    값이 없으면(센서 미연결) 해당 항목은 None이다.
    """

    __slots__ = ("light", "temperature_c", "pressure_hpa", "humidity")

    def __init__(self, light=None, temperature_c=None,
                 pressure_hpa=None, humidity=None) -> None:
        self.light = light                # 0.0(캄캄) ~ 1.0(매우 밝음) 또는 None
        self.temperature_c = temperature_c
        self.pressure_hpa = pressure_hpa  # DHT11은 기압 미측정 → 항상 None (자리만 유지)
        self.humidity = humidity          # 상대습도 % (DHT11). 센서 없으면 None

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


class _DHT11:
    """DHT11 온도·습도 센서 드라이버 (lgpio 커널 엣지캡처, 외부 의존성 없음).

    단선(1-wire 방식) 프로토콜을 직접 디코딩한다.
      ① 호스트가 데이터선을 ≥18ms LOW로 끌어 시작을 알린다.
      ② 입력으로 전환하면 센서가 응답(80µs LOW + 80µs HIGH) 후 40비트를 보낸다.
      ③ 각 비트 = 50µs LOW + HIGH(약 26µs='0', 약 70µs='1'). HIGH 길이로 0/1을 가른다.
      ④ 5바이트(습도정수·습도소수·온도정수·온도소수·체크섬), 끝에 체크섬으로 검증.

    µs급 펄스는 파이썬 폴링으로 못 잡으므로(놓치거나 게임 루프가 멈춤), lgpio
    alert로 **커널이 엣지 시각을 타임스탬프**하게 한다(파이썬 속도와 무관). 캡처는
    고정 시간이라 센서가 무응답이어도 절대 멈추지 않는다. read()는 성공할 때까지
    retries회 재시도하고, 모두 실패하면 예외를 던져 호출부가 폴백한다.
    """

    def __init__(self, gpio: int, retries: int = 5) -> None:
        self._gpio = gpio
        self._retries = max(1, retries)
        self._chip = lgpio.gpiochip_open(0)

    def close(self) -> None:
        try:
            lgpio.gpiochip_close(self._chip)
        except Exception:
            pass

    def read(self) -> tuple[float, float]:
        """(온도℃, 습도%)를 반환한다. 모든 재시도가 실패하면 예외."""
        last_err = None
        for _ in range(self._retries):
            try:
                return self._decode(self._sample())
            except Exception as e:   # 무응답·체크섬 실패 → 잠시 쉬고 재시도
                last_err = e
                time.sleep(0.02)
        raise last_err if last_err is not None else RuntimeError("DHT11 읽기 실패")

    def _sample(self) -> list:
        """시작 신호를 보낸 뒤, 커널이 타임스탬프한 엣지 목록 [(level, tick_ns), …]를 반환.

        파이썬 폴링 대신 lgpio alert로 커널이 엣지를 기록하므로 µs급 펄스도 놓치지
        않고, 고정 대기(캡처 시간)라 센서가 무응답이어도 멈추지 않는다.
        """
        chip, pin = self._chip, self._gpio
        edges: list = []
        lgpio.gpio_claim_output(chip, pin, 0)    # ① ≥18ms LOW 시작 신호
        time.sleep(0.020)
        # ② 입력+양엣지 캡처로 전환 → 풀업이 라인을 올리면 센서가 응답을 시작한다.
        lgpio.gpio_claim_alert(chip, pin, lgpio.BOTH_EDGES)
        cb = lgpio.callback(chip, pin, lgpio.BOTH_EDGES,
                            lambda c, g, level, tick: edges.append((level, tick)))
        try:
            time.sleep(0.01)                     # 응답+40비트 ≈ 4ms → 넉넉히 10ms
        finally:
            cb.cancel()
            lgpio.gpio_free(chip, pin)
        return edges

    @staticmethod
    def _decode(edges: list) -> tuple[float, float]:
        """엣지 타임스탬프에서 40비트를 복원해 (온도℃, 습도%)로 변환한다."""
        if len(edges) < 82:                      # 응답 2 + 40비트×2 ≈ 82엣지
            raise RuntimeError(f"DHT11 무응답/불완전(엣지 {len(edges)}개)")
        # 데이터는 HIGH 펄스 길이에 실린다. 상승(level=1)→다음 하강(level=0) 간격을 잰다.
        highs = []
        for i in range(1, len(edges)):
            (lvl_prev, t_prev), (lvl, t) = edges[i - 1], edges[i]
            if lvl_prev == 1 and lvl == 0:
                highs.append(t - t_prev)
        if len(highs) < 40:
            raise RuntimeError(f"DHT11 비트 부족({len(highs)})")
        bits = highs[-40:]                       # 마지막 40개가 데이터(앞은 핸드셰이크)
        threshold = (min(bits) + max(bits)) / 2.0
        data = bytearray(5)
        for i, width in enumerate(bits):
            if width > threshold:                # 긴 HIGH = '1'
                data[i // 8] |= 1 << (7 - (i % 8))
        if ((data[0] + data[1] + data[2] + data[3]) & 0xFF) != data[4]:
            raise RuntimeError("DHT11 체크섬 불일치")
        humidity = data[0] + data[1] * 0.1
        temp = data[2] + (data[3] & 0x7F) * 0.1
        if data[3] & 0x80:                       # 최상위 비트 = 음수 온도(영하)
            temp = -temp
        return float(temp), float(humidity)


class Environment:
    """조도 + 온도/습도 센서 묶음. 어느 한쪽만 연결돼도 동작한다."""

    def __init__(self) -> None:
        self._ldr = None
        self._dht = None
        if _ADC_AVAILABLE:
            try:
                self._ldr = MCP3008(channel=config.ADC_CHANNEL_LIGHT)
            except Exception:
                self._ldr = None
        if _DHT_AVAILABLE:
            try:
                self._dht = _DHT11(config.DHT11_GPIO, retries=config.DHT11_RETRIES)
            except Exception:
                self._dht = None

    @property
    def available(self) -> bool:
        return self._ldr is not None or self._dht is not None

    @property
    def light_available(self) -> bool:
        return self._ldr is not None

    @property
    def temp_available(self) -> bool:
        return self._dht is not None

    def light(self):
        """조도 0.0(캄캄)~1.0(밝음). 센서 없으면 None."""
        if self._ldr is None:
            return None
        v = float(self._ldr.value)
        return 1.0 - v if config.LIGHT_INVERT else v

    def read(self) -> EnvReading:
        """현재 환경을 한 번에 읽어 스냅샷으로 반환한다."""
        light = self.light()
        temp = humidity = None
        if self._dht is not None:
            try:
                temp, humidity = self._dht.read()
            except Exception:
                temp = humidity = None
        # 기압: DHT11은 미측정 → 항상 None.
        return EnvReading(light=light, temperature_c=temp,
                          pressure_hpa=None, humidity=humidity)


class DummyEnvironment(Environment):
    """센서가 없을 때 쓰는 더미 — 모든 값이 None(중립)."""

    def __init__(self) -> None:
        self._ldr = None
        self._dht = None

    def read(self) -> EnvReading:
        return EnvReading()


def create_environment() -> Environment:
    """가능하면 실제 센서, 아니면 더미를 반환한다."""
    if config.USE_DUMMY_HARDWARE:
        return DummyEnvironment()
    env = Environment()
    return env if env.available else DummyEnvironment()
