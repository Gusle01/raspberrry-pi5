"""초음파 거리 센서 (HC-SR04).

손까지의 거리를 cm 단위로 측정한다. (계획서 4.2.3)
하드웨어가 없으면 더미(먼 거리 고정) 구현으로 폴백한다.
"""
from .. import config

try:
    from gpiozero import DistanceSensor
    _GPIO_AVAILABLE = True
except Exception:
    _GPIO_AVAILABLE = False


class Ultrasonic:
    """HC-SR04 래퍼."""

    def __init__(self) -> None:
        self._sensor = None
        if _GPIO_AVAILABLE:
            # max_distance(m)는 점프 게임 매핑 상한보다 넉넉히 잡는다.
            self._sensor = DistanceSensor(
                echo=config.PIN_ULTRASONIC_ECHO,
                trigger=config.PIN_ULTRASONIC_TRIG,
                max_distance=1.0,
            )

    @property
    def available(self) -> bool:
        return self._sensor is not None

    def distance_cm(self) -> float:
        """현재 거리(cm)를 반환한다. 센서가 없으면 최대치(먼 거리)."""
        if self._sensor is None:
            return float(config.JUMP_DISTANCE_MAX_CM)
        return self._sensor.distance * 100.0  # m → cm


class DummyUltrasonic(Ultrasonic):
    """장치가 없을 때 사용하는 더미 센서."""

    def __init__(self) -> None:
        self._sensor = None


def create_ultrasonic() -> Ultrasonic:
    """가능하면 실제 센서, 아니면 더미를 반환한다."""
    if config.USE_DUMMY_HARDWARE:
        return DummyUltrasonic()
    if _GPIO_AVAILABLE:
        try:
            return Ultrasonic()
        except Exception:
            pass
    return DummyUltrasonic()
