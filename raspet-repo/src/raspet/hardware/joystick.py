"""아날로그 조이스틱 입력 (MCP3008 ADC, SPI).

라즈베리파이에는 아날로그 입력이 없어 ADC로 전압값을 읽는다.
(계획서 3.1 / 6장)

gpiozero/하드웨어가 없으면 더미(중립) 구현으로 폴백한다.
"""
from .. import config

try:
    from gpiozero import MCP3008, Button
    _GPIO_AVAILABLE = True
except Exception:
    _GPIO_AVAILABLE = False


class Joystick:
    """MCP3008을 통해 2축 조이스틱 값을 읽는다."""

    def __init__(self) -> None:
        self._adc_x = None
        self._adc_y = None
        self._button = None      # GPIO 디지털 버튼
        self._adc_button = None  # ADC(아날로그) 버튼
        if _GPIO_AVAILABLE:
            self._adc_x = MCP3008(channel=config.ADC_CHANNEL_X)
            self._adc_y = MCP3008(channel=config.ADC_CHANNEL_Y)
            btn_ch = getattr(config, "ADC_CHANNEL_BUTTON", None)
            if btn_ch is not None:
                # SW를 같은 MCP3008의 아날로그 채널에서 읽는다(배선에 맞춤).
                self._adc_button = MCP3008(channel=btn_ch)
            elif config.PIN_JOYSTICK_BUTTON is not None:
                self._button = Button(config.PIN_JOYSTICK_BUTTON)

    @property
    def available(self) -> bool:
        return self._adc_x is not None

    def read(self) -> tuple[float, float]:
        """(x, y)를 -1.0 ~ 1.0 범위로 반환한다. (가운데가 0)"""
        if self._adc_x is None:
            return (0.0, 0.0)
        # MCP3008.value 는 0.0~1.0 → -1.0~1.0 으로 변환
        x = self._adc_x.value * 2.0 - 1.0
        y = self._adc_y.value * 2.0 - 1.0
        if getattr(config, "JOYSTICK_INVERT_Y", False):
            y = -y                      # 배선상 위/아래 반전 보정
        return (x, y)

    def direction(self) -> str:
        """입력을 'up'/'down'/'left'/'right'/'center' 로 단순화한다."""
        x, y = self.read()
        dz = config.JOYSTICK_DEADZONE
        if abs(x) < dz and abs(y) < dz:
            return "center"
        if abs(x) >= abs(y):
            return "right" if x > 0 else "left"
        # y축은 위가 양수가 되도록 가정(배선에 맞게 조정)
        return "up" if y > 0 else "down"

    def pressed(self) -> bool:
        """조이스틱 버튼이 눌렸는지. ADC 버튼이 있으면 임계값으로, 없으면 GPIO로 판정.

        ADC(CH0)는 풀업이 없어 안 누른 상태에서도 값이 출렁인다. 단일 표본으로
        판정하면 순간 튐에 헛인식하므로, 여러 번 읽어 *중앙값*이 임계 미만일 때만
        눌림으로 본다(중앙값은 한두 표본의 스파이크에 흔들리지 않는다).
        """
        if self._adc_button is not None:
            n = max(1, getattr(config, "ADC_BUTTON_SAMPLES", 5))
            vals = sorted(self._adc_button.value for _ in range(n))
            median = vals[n // 2]
            return median < config.ADC_BUTTON_PRESSED_BELOW
        return bool(self._button and self._button.is_pressed)


class DummyJoystick(Joystick):
    """장치가 없을 때 사용하는 중립 조이스틱."""

    def __init__(self) -> None:
        self._adc_x = None
        self._adc_y = None
        self._button = None
        self._adc_button = None


def create_joystick() -> Joystick:
    """가능하면 실제 조이스틱, 아니면 더미를 반환한다."""
    if config.USE_DUMMY_HARDWARE:
        return DummyJoystick()
    if _GPIO_AVAILABLE:
        try:
            return Joystick()
        except Exception:
            pass
    return DummyJoystick()
