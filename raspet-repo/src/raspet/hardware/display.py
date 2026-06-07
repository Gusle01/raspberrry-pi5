"""OLED 디스플레이 출력 (luma.oled + Pillow).

Pygame으로 그린 프레임을 받아 OLED로 전송한다.
디스플레이 종류(SSD1306/SSD1309/SSD1351/ST7789)는 사양 확정 후 선택. (계획서 5.3)
"""


class Display:
    """OLED 출력 래퍼."""

    def __init__(self) -> None:
        # TODO: luma.oled 디바이스 초기화 (인터페이스/드라이버 선택)
        self._device = None

    def show(self, image) -> None:
        """PIL 이미지를 화면에 출력한다."""
        # TODO: self._device.display(image)
        raise NotImplementedError

    def clear(self) -> None:
        # TODO: 화면 지우기
        pass
