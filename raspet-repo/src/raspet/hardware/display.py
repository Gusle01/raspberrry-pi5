"""OLED 디스플레이 출력 (luma.oled + Pillow).

Pygame으로 그린 프레임을 PIL 이미지로 변환해 OLED로 전송한다.
디스플레이 종류(SSD1306/SSD1309/SSD1351/ST7789)는 사양 확정 후 선택. (계획서 5.3)

하드웨어/라이브러리가 없으면 자동으로 더미(no-op) 구현으로 폴백하므로
PC에서도 임포트·실행이 깨지지 않는다.
"""
from .. import config

try:  # 실제 OLED 라이브러리 (Pi에서만 설치되는 경우가 많다)
    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306
    _LUMA_AVAILABLE = True
except Exception:  # ImportError 외에 SPI/I2C 미설정 등도 포함
    _LUMA_AVAILABLE = False


class Display:
    """OLED 출력 래퍼. PIL 이미지를 받아 화면에 표시한다."""

    def __init__(self) -> None:
        self._device = None
        if _LUMA_AVAILABLE:
            serial = i2c(port=1, address=0x3C)
            self._device = ssd1306(serial,
                                   width=config.GAME_W,
                                   height=config.GAME_H)

    @property
    def available(self) -> bool:
        return self._device is not None

    def show(self, image) -> None:
        """PIL 이미지를 화면에 출력한다."""
        if self._device is not None:
            self._device.display(image.convert(self._device.mode))

    def clear(self) -> None:
        if self._device is not None:
            self._device.clear()


class DummyDisplay(Display):
    """장치가 없을 때 사용하는 no-op 디스플레이."""

    def __init__(self) -> None:
        self._device = None

    def show(self, image) -> None:  # 화면 없음 → 무시
        pass


def create_display() -> Display:
    """가능하면 실제 OLED, 아니면 더미 디스플레이를 반환한다."""
    if config.USE_DUMMY_HARDWARE:
        return DummyDisplay()
    if _LUMA_AVAILABLE:
        try:
            return Display()
        except Exception:
            pass
    return DummyDisplay()
