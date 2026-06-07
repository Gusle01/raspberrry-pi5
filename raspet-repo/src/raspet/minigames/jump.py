"""초음파 점프 게임 (제안).

초음파 센서로 손의 높이(거리)를 읽어 캐릭터의 점프 높이를 제어,
다가오는 장애물을 피한다. (계획서 4.2.3)
"""
from .base import MiniGame


class UltrasonicJump(MiniGame):
    name = "초음파 점프"

    def play(self) -> int:
        # TODO: hardware.ultrasonic 거리 → 캐릭터 높이 매핑, 장애물 충돌 판정
        raise NotImplementedError
