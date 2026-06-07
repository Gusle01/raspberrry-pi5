"""초음파 거리 센서 (HC-SR04).

손까지의 거리를 cm 단위로 측정한다. (계획서 4.2.3)
"""
from .. import config


class Ultrasonic:
    """HC-SR04 래퍼."""

    def __init__(self) -> None:
        # TODO: gpiozero.DistanceSensor(echo=..., trigger=...) 초기화
        pass

    def distance_cm(self) -> float:
        """현재 거리(cm)를 반환한다."""
        # TODO: 거리 측정
        raise NotImplementedError
