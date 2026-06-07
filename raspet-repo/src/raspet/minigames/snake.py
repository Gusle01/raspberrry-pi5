"""조이스틱 미니게임 (제안): 스네이크 / 떨어지는 아이템 받기.

단순 흑백·저해상도 화면에 적합. (계획서 4.2.4)
"""
from .base import MiniGame


class Snake(MiniGame):
    name = "스네이크"

    def play(self) -> int:
        # TODO: 조이스틱 방향 입력, 먹이 섭취, 자기 몸/벽 충돌 판정
        raise NotImplementedError
