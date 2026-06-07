"""아날로그 조이스틱 입력 (MCP3008 ADC, SPI).

라즈베리파이에는 아날로그 입력이 없어 ADC로 전압값을 읽는다.
(계획서 3.1 / 6장)
"""
from .. import config


class Joystick:
    """MCP3008을 통해 2축 조이스틱 값을 읽는다."""

    def __init__(self) -> None:
        # TODO: gpiozero.MCP3008(channel=...) 또는 spidev 초기화
        pass

    def read(self) -> tuple[float, float]:
        """(x, y)를 -1.0 ~ 1.0 범위로 반환한다."""
        # TODO: ADC 채널(config.ADC_CHANNEL_X/Y) 읽어 정규화
        raise NotImplementedError

    def direction(self) -> str:
        """입력을 'up'/'down'/'left'/'right'/'center' 로 단순화한다."""
        raise NotImplementedError
