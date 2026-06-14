"""오목 (AI 대전 · 필수).

조이스틱으로 커서를 움직여 돌을 놓고, ai.omok_ai 와 번갈아 둔다.
먼저 5목을 만들면 승리. (계획서 4.2.2 / 5.2)

하드웨어 없이 테스트할 수 있도록 입력과 출력을 주입(injection)받는다.
- move_provider(board) -> (row, col): 사람 플레이어의 다음 착수 좌표
- renderer(board, info): (선택) 매 턴 화면을 그린다
실제 기기에서는 조이스틱 커서 입력기와 OLED 렌더러를 넣어 사용한다.
"""
from .base import MiniGame
from ..ai.omok_ai import OmokAI
from .. import config

EMPTY = 0
HUMAN = 1   # 사람(선공)
AI = 2      # 컴퓨터


class Omok(MiniGame):
    name = "오목"

    def __init__(self, difficulty: str = "normal",
                 move_provider=None, renderer=None) -> None:
        self.size = config.OMOK_BOARD_SIZE
        self.board = [[EMPTY] * self.size for _ in range(self.size)]
        self.ai = OmokAI(difficulty=difficulty, ai_stone=AI, human_stone=HUMAN)
        self.move_provider = move_provider
        self.renderer = renderer
        self.winner = None  # None=미정, HUMAN/AI=승자, EMPTY=무승부

    # ── 보드 조작 ───────────────────────────────────────
    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.size and 0 <= c < self.size

    def is_valid(self, r: int, c: int) -> bool:
        """빈 칸이고 판 안에 있으면 둘 수 있다."""
        return self.in_bounds(r, c) and self.board[r][c] == EMPTY

    def place(self, r: int, c: int, stone: int) -> None:
        """돌을 놓는다. 유효하지 않으면 ValueError."""
        if not self.is_valid(r, c):
            raise ValueError(f"착수 불가 좌표: ({r}, {c})")
        self.board[r][c] = stone

    def is_full(self) -> bool:
        return all(self.board[r][c] != EMPTY
                   for r in range(self.size) for c in range(self.size))

    def check_win(self, r: int, c: int) -> bool:
        """(r, c)의 돌이 5목을 완성했는지 검사한다."""
        stone = self.board[r][c]
        if stone == EMPTY:
            return False
        return self.ai._is_win_at(self.board, r, c, stone)

    # ── 게임 진행 ───────────────────────────────────────
    def play(self) -> int:
        """턴 루프를 돌리고 결과에 따른 획득 재화를 반환한다.

        사람(선공) → 승리 체크 → AI 착수 → 승리 체크 순으로 반복한다.
        """
        if self.move_provider is None:
            raise RuntimeError("move_provider가 필요하다 (사람 입력기 주입).")

        self._render({"turn": "start"})
        while True:
            # 1) 사람 차례 (유효한 수가 나올 때까지 받는다)
            r, c = self._ask_human_move()
            self.place(r, c, HUMAN)
            self._render({"turn": "human", "last": (r, c)})
            if self.check_win(r, c):
                self.winner = HUMAN
                break
            if self.is_full():
                self.winner = EMPTY
                break

            # 2) AI 차례
            ar, ac = self.ai.best_move(self.board)
            self.place(ar, ac, AI)
            self._render({"turn": "ai", "last": (ar, ac)})
            if self.check_win(ar, ac):
                self.winner = AI
                break
            if self.is_full():
                self.winner = EMPTY
                break

        self._render({"turn": "end", "winner": self.winner})
        return self._reward()

    def _ask_human_move(self) -> tuple[int, int]:
        """유효한 착수 좌표를 받을 때까지 입력기를 호출한다."""
        while True:
            r, c = self.move_provider(self.board)
            if self.is_valid(r, c):
                return r, c
            # 잘못된 입력은 무시하고 다시 요청한다.

    def _reward(self) -> int:
        if self.winner == HUMAN:
            return config.OMOK_WIN_REWARD
        if self.winner == AI:
            return config.OMOK_LOSE_REWARD
        return config.OMOK_DRAW_REWARD

    def _render(self, info: dict) -> None:
        if self.renderer is not None:
            self.renderer(self.board, info)
