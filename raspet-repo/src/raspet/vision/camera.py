"""카메라 캡처 (picamera2).

CSI 카메라에서 프레임을 가져온다.
picamera2가 없으면 더미(빈 프레임) 구현으로 폴백한다.
"""
try:
    from picamera2 import Picamera2
    _CAM_AVAILABLE = True
except Exception:
    _CAM_AVAILABLE = False


class Camera:
    """picamera2 래퍼."""

    def __init__(self) -> None:
        self._cam = None
        if _CAM_AVAILABLE:
            # 센서가 실제로 붙어 있지 않으면 Picamera2() 생성자가 멈추거나
            # 예외를 던지므로, 먼저 빠르게 카메라 목록을 확인한다.
            if not Picamera2.global_camera_info():
                raise RuntimeError("No cameras available")
            self._cam = Picamera2()
            cfg = self._cam.create_preview_configuration(
                main={"format": "RGB888", "size": (640, 480)})
            self._cam.configure(cfg)
            self._cam.start()

    @property
    def available(self) -> bool:
        return self._cam is not None

    def capture_frame(self):
        """현재 프레임(numpy 배열, RGB)을 반환한다. 없으면 None."""
        if self._cam is None:
            return None
        return self._cam.capture_array()

    def close(self) -> None:
        if self._cam is not None:
            self._cam.stop()
            self._cam = None


class DummyCamera(Camera):
    """카메라가 없을 때 사용하는 더미."""

    def __init__(self) -> None:
        self._cam = None

    def capture_frame(self):
        return None


def create_camera() -> Camera:
    """가능하면 실제 카메라, 아니면 더미를 반환한다."""
    from .. import config
    if config.USE_DUMMY_HARDWARE:
        return DummyCamera()
    if _CAM_AVAILABLE:
        try:
            return Camera()
        except Exception:
            pass
    return DummyCamera()
