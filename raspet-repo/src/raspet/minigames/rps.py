"""가위바위보 (카메라 활용 · 필수).

카메라로 손을 촬영 → vision.hand 로 가위/바위/보 인식 →
컴퓨터의 무작위 선택과 비교해 승패 판정. (계획서 4.2.1 / 5.1)
"""
import random

from .base import MiniGame

CHOICES = ("rock", "scissors", "paper")


class RockPaperScissors(MiniGame):
    name = "가위바위보"

    def play(self) -> int:
        user = self._read_user_hand()      # TODO: vision.hand 연동
        com = random.choice(CHOICES)
        # TODO: 승패 판정 및 재화 지급
        raise NotImplementedError

    def _read_user_hand(self) -> str:
        """카메라 프레임에서 사용자의 수를 인식한다."""
        # TODO: vision.hand.classify_gesture() 호출
        raise NotImplementedError
