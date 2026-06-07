"""오목 (AI 대전 · 필수).

조이스틱으로 커서를 움직여 돌을 놓고, ai.omok_ai 와 번갈아 둔다.
먼저 5목을 만들면 승리. (계획서 4.2.2 / 5.2)
"""
from .base import MiniGame
from ..ai.omok_ai import OmokAI

BOARD_SIZE = 15


class Omok(MiniGame):
    name = "오목"

    def __init__(self, difficulty: str = "normal") -> None:
        self.board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.ai = OmokAI(difficulty=difficulty)

    def play(self) -> int:
        # TODO: 턴 루프 (플레이어 입력 → 승리 체크 → AI 착수 → 승리 체크)
        raise NotImplementedError
