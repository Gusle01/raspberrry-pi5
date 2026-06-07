"""카메라 색깔 찾기 (제안).

제시된 색을 띤 주변 사물을 카메라에 비추면 OpenCV 색상 인식으로 판정.
(계획서 4.2.5)
"""
from .base import MiniGame


class ColorHunt(MiniGame):
    name = "색깔 찾기"

    def play(self) -> int:
        # TODO: 목표 색 제시 → HSV 변환 + 임계값으로 해당 색 검출
        raise NotImplementedError
