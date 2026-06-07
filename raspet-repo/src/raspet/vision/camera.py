"""카메라 캡처 (picamera2).

CSI 카메라에서 프레임을 가져온다.
"""


class Camera:
    """picamera2 래퍼."""

    def __init__(self) -> None:
        # TODO: Picamera2 초기화 및 설정
        self._cam = None

    def capture_frame(self):
        """현재 프레임(numpy 배열)을 반환한다."""
        # TODO: 프레임 캡처
        raise NotImplementedError

    def close(self) -> None:
        # TODO: 카메라 해제
        pass
