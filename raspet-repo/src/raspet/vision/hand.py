"""손 인식 — 가위/바위/보 분류.

1순위: MediaPipe Hands (21개 랜드마크로 펴진 손가락 판별)
대체:  MediaPipe 사용 불가 시 OpenCV 윤곽선 + 볼록 결함 분석
(계획서 5.1)
"""

# 펴진 손가락 개수 → 제스처
#   0개 = 바위(rock), 2개(검지·중지) = 가위(scissors), 5개 = 보(paper)


class HandRecognizer:
    """손 모양을 인식해 'rock' / 'scissors' / 'paper' 중 하나로 분류한다."""

    def __init__(self, use_mediapipe: bool = True) -> None:
        self.use_mediapipe = use_mediapipe
        # TODO: MediaPipe Hands 초기화 (실패 시 use_mediapipe=False 로 폴백)

    def classify_gesture(self, frame) -> str | None:
        """프레임에서 제스처를 인식한다. 인식 실패 시 None."""
        if self.use_mediapipe:
            return self._classify_mediapipe(frame)
        return self._classify_opencv(frame)

    def _classify_mediapipe(self, frame) -> str | None:
        # TODO: 랜드마크 추출 → 펴진 손가락 수 계산 → 제스처 매핑
        raise NotImplementedError

    def _classify_opencv(self, frame) -> str | None:
        # TODO: 피부색 마스킹 → 윤곽선/볼록결함 → 손가락 수 계산
        raise NotImplementedError
