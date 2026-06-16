"""손 인식 — 가위/바위/보 분류.

1순위: MediaPipe Hands (21개 랜드마크로 펴진 손가락 판별)
대체:  MediaPipe 사용 불가 시 OpenCV 윤곽선 + 볼록 결함 분석
둘 다 없으면 더미(None 반환)로 폴백한다. (계획서 5.1)

펴진 손가락 개수 → 제스처
  0~1개 = 바위(rock), 2~3개 = 가위(scissors), 4~5개 = 보(paper)
"""
import math

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

        손이 기울어져도 동작하도록 y좌표 대신 *손목(landmark 0)까지의 거리*로
        판정한다. 펴진 손가락은 끝(tip)이 둘째 마디(pip)보다 손목에서 멀다 —
        이 관계는 손의 회전과 무관하므로, 주먹을 눕혀도 가위로 튀지 않는다.

        엄지: 손가락처럼 말리지 않으므로 끝(4)이 검지 밑동(5)에서 충분히
        떨어졌는지로 판정한다. 주먹 쥐면 엄지 끝이 손바닥 쪽으로 접혀 가까워진다.
        """
        def d(a, b):
            return math.hypot(lm[a].x - lm[b].x, lm[a].y - lm[b].y)

        count = 0
        # 검지~새끼: tip이 pip보다 손목(0)에서 멀면 펴진 것
        for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
            if d(tip, 0) > d(pip, 0):
                count += 1
        # 엄지: 끝(4)-검지밑동(5) 거리가 IP관절(3)-검지밑동(5)보다 크면 펴진 것
        if d(4, 5) > d(3, 5):
            count += 1
        return count

    def _classify_opencv(self, frame) -> str | None:
        count = self._count_fingers_opencv(frame)
        if count is None:
            return None
        return fingers_to_gesture(count)

    # OpenCV 백엔드 임계값(진단 도구 tools/rps_probe.py 로 실측·보정)
    OPENCV_MIN_AREA = 3000      # 손으로 인정할 최소 윤곽 면적(px)
    OPENCV_ROCK_SOLIDITY = 0.90  # 이 이상이면 주먹으로 직결
    OPENCV_DEFECT_DEPTH = 20     # 손가락 사이 골로 인정할 최소 깊이(px)

    @classmethod
    def analyze_opencv(cls, frame):
        """OpenCV 경로의 중간 신호까지 모두 담은 진단 dict를 돌려준다.

        반환: {count, area, solidity, deep, reason}. count가 None이면 손 미검출.
        실제 분류(_count_fingers_opencv)와 진단 도구가 같은 로직을 공유하도록
        단일 소스로 둔다. reason은 어떤 규칙으로 count가 정해졌는지 설명.
        """
        ycrcb = cv2.cvtColor(frame, cv2.COLOR_RGB2YCrCb)
        mask = cv2.inRange(ycrcb, (0, 133, 77), (255, 173, 127))
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        # 잡음/구멍 정리: 열림→닫힘으로 마스크 안정화
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        info = {"count": None, "area": 0.0, "solidity": 0.0,
                "deep": 0, "reason": "no-contour"}
        if not contours:
            return info
        cnt = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(cnt)
        info["area"] = area
        if area < cls.OPENCV_MIN_AREA:
            info["reason"] = "area<min"
            return info
        hull_pts = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull_pts)
        solidity = area / hull_area if hull_area > 0 else 1.0
        info["solidity"] = solidity
        # 꽉 찬 손모양(solidity 높음) = 주먹. 펴진 손가락은 골 때문에 낮아진다.
        if solidity > cls.OPENCV_ROCK_SOLIDITY:
            info.update(count=0, reason="solidity→rock")
            return info
        hull = cv2.convexHull(cnt, returnPoints=False)
        if hull is None or len(hull) < 3:
            info.update(count=0, reason="no-hull→rock")
            return info
        defects = cv2.convexityDefects(cnt, hull)
        if defects is None:
            info.update(count=0, reason="no-defects→rock")
            return info
        # 손가락 사이의 깊은 골(defect) 개수 + 1 ≈ 펴진 손가락 수
        deep = 0
        for i in range(defects.shape[0]):
            depth = defects[i, 0, 3] / 256.0
            if depth > cls.OPENCV_DEFECT_DEPTH:
                deep += 1
        info["deep"] = deep
        if deep == 0:          # 골이 전혀 없으면 주먹으로 본다
            info.update(count=0, reason="deep=0→rock")
            return info
        info.update(count=min(deep + 1, 5), reason="deep+1")
        return info

    @classmethod
    def _count_fingers_opencv(cls, frame):
        """피부색 마스킹 → 윤곽선·solidity·볼록결함으로 손가락 수를 추정한다."""
        return cls.analyze_opencv(frame)["count"]


def create_hand_recognizer(use_mediapipe: bool = True) -> HandRecognizer:
    """가능한 백엔드로 손 인식기를 만든다 (없으면 더미)."""
    return HandRecognizer(use_mediapipe=use_mediapipe)
