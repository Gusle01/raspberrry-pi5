"""손 인식 — 가위/바위/보 분류.

1순위: MediaPipe Hands (21개 랜드마크로 펴진 손가락 판별)
대체:  MediaPipe 사용 불가 시 OpenCV 윤곽선 + 볼록 결함 분석
둘 다 없으면 더미(None 반환)로 폴백한다. (계획서 5.1)

펴진 손가락 개수 → 제스처
  0~1개 = 바위(rock), 2~3개 = 가위(scissors), 4~5개 = 보(paper)
"""
try:
    import mediapipe as mp
    _MP_AVAILABLE = True
except Exception:
    _MP_AVAILABLE = False

try:
    import cv2
    import numpy as np
    _CV_AVAILABLE = True
except Exception:
    _CV_AVAILABLE = False


def majority_gesture(gestures):
    """여러 프레임의 인식 결과 중 최빈 제스처를 반환한다.

    단일 프레임은 흔들림/노이즈로 오인식하기 쉬우므로, 짧은 구간 동안 모은 여러
    인식 결과를 다수결로 합쳐 안정성을 높인다. 유효 인식이 하나도 없으면 None.
    동점이면 먼저 등장한 제스처를 택한다(Counter가 등장 순서를 보존).
    """
    from collections import Counter
    valid = [g for g in gestures if g in ("rock", "scissors", "paper")]
    if not valid:
        return None
    return Counter(valid).most_common(1)[0][0]


def fingers_to_gesture(n: int) -> str:
    """펴진 손가락 수를 가위바위보 제스처로 매핑한다."""
    if n <= 1:
        return "rock"
    if n <= 3:
        return "scissors"
    return "paper"


class HandRecognizer:
    """손 모양을 인식해 'rock' / 'scissors' / 'paper' 중 하나로 분류한다."""

    def __init__(self, use_mediapipe: bool = True) -> None:
        self.backend = None
        self._hands = None
        if use_mediapipe and _MP_AVAILABLE:
            self._hands = mp.solutions.hands.Hands(
                static_image_mode=True, max_num_hands=1,
                min_detection_confidence=0.5)
            self.backend = "mediapipe"
        elif _CV_AVAILABLE:
            self.backend = "opencv"
        # 둘 다 없으면 backend=None (더미)

    @property
    def available(self) -> bool:
        return self.backend is not None

    def classify_gesture(self, frame) -> str | None:
        """프레임에서 제스처를 인식한다. 인식 실패 시 None."""
        if frame is None:
            return None
        if self.backend == "mediapipe":
            return self._classify_mediapipe(frame)
        if self.backend == "opencv":
            return self._classify_opencv(frame)
        return None

    def _classify_mediapipe(self, frame) -> str | None:
        result = self._hands.process(frame)
        if not result.multi_hand_landmarks:
            return None
        lm = result.multi_hand_landmarks[0].landmark
        count = self._count_fingers_mediapipe(lm)
        return fingers_to_gesture(count)

    @staticmethod
    def _count_fingers_mediapipe(lm) -> int:
        """랜드마크에서 펴진 손가락 수를 센다.

        검지~새끼: 끝(tip)이 둘째 마디(pip)보다 위(y가 작음)이면 펴진 것.
        엄지: 끝이 관절보다 바깥(x)으로 나가면 펴진 것(대략).
        """
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        count = 0
        for tip, pip in zip(tips, pips):
            if lm[tip].y < lm[pip].y:
                count += 1
        # 엄지(좌우 방향 비교)
        if abs(lm[4].x - lm[2].x) > abs(lm[3].x - lm[2].x):
            count += 1
        return count

    def _classify_opencv(self, frame) -> str | None:
        count = self._count_fingers_opencv(frame)
        if count is None:
            return None
        return fingers_to_gesture(count)

    @staticmethod
    def _count_fingers_opencv(frame):
        """피부색 마스킹 → 최대 윤곽선 → 볼록결함으로 손가락 수를 추정한다."""
        ycrcb = cv2.cvtColor(frame, cv2.COLOR_RGB2YCrCb)
        mask = cv2.inRange(ycrcb, (0, 133, 77), (255, 173, 127))
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        cnt = max(contours, key=cv2.contourArea)
        if cv2.contourArea(cnt) < 3000:
            return None
        hull = cv2.convexHull(cnt, returnPoints=False)
        if hull is None or len(hull) < 3:
            return 0
        defects = cv2.convexityDefects(cnt, hull)
        if defects is None:
            return 0
        # 손가락 사이의 깊은 골(defect) 개수 + 1 ≈ 펴진 손가락 수
        deep = 0
        for i in range(defects.shape[0]):
            depth = defects[i, 0, 3] / 256.0
            if depth > 20:
                deep += 1
        return min(deep + 1, 5)


def create_hand_recognizer(use_mediapipe: bool = True) -> HandRecognizer:
    """가능한 백엔드로 손 인식기를 만든다 (없으면 더미)."""
    return HandRecognizer(use_mediapipe=use_mediapipe)
