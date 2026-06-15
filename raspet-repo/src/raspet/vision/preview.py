"""카메라 미리보기 창 — 카메라 미니게임 중 실제 카메라 화면을 별도 창에 띄운다.

OLED/게임 미리보기 창에는 128×64 게임 화면이 나가고, 이 창에는 카메라 원본
프레임이 표시된다(가위바위보·색깔 찾기 등에서 "내가 무엇을 비추고 있는지" 보이게).

OpenCV(cv2)로 창을 띄운다. cv2가 없거나 헤드리스/프레임이 없으면 조용히 무시한다.
"""
from .. import config

try:
    import cv2
    import numpy as np
    _CV_AVAILABLE = True
except Exception:
    _CV_AVAILABLE = False


class CameraPreview:
    """카메라 프레임을 OS 창 하나에 계속 갱신해 보여준다."""

    def __init__(self, title: str | None = None, size=None) -> None:
        self.title = title or config.CAMERA_PREVIEW_TITLE
        self.size = size if size is not None else config.CAMERA_PREVIEW_SIZE
        self._open = False

    @property
    def available(self) -> bool:
        return _CV_AVAILABLE and config.CAMERA_PREVIEW

    def show(self, frame, label: str | None = None) -> None:
        """RGB 프레임을 창에 표시한다. frame이 None이면 아무것도 하지 않는다.

        label을 주면 화면 위에 안내 문구를 겹쳐 그린다(예: 인식된 손 모양).
        """
        if not self.available or frame is None:
            return
        try:
            img = np.asarray(frame)
            if img.ndim == 3 and img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)   # picamera2는 RGB, cv2는 BGR
            if self.size is not None:
                img = cv2.resize(img, tuple(self.size))
            if label:
                cv2.putText(img, str(label), (8, 24), cv2.FONT_HERSHEY_SIMPLEX,
                            0.7, (40, 220, 120), 2, cv2.LINE_AA)
            cv2.imshow(self.title, img)
            cv2.waitKey(1)            # GUI 이벤트 펌프(이게 없으면 창이 안 그려진다)
            self._open = True
        except Exception:
            # 미리보기는 부가 기능이므로 실패해도 게임은 계속 진행한다.
            pass

    def close(self) -> None:
        """미리보기 창을 닫는다(미니게임 종료 시)."""
        if not _CV_AVAILABLE or not self._open:
            return
        try:
            cv2.destroyWindow(self.title)
            cv2.waitKey(1)
        except Exception:
            pass
        self._open = False
