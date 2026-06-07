"""오목 대전 AI — Minimax + 알파-베타 가지치기.

학습 모델 없이 탐색 기반으로 구현한다. 돌의 연결 형태(열린 2·열린 3·4 등)에
점수를 부여하는 평가 함수로 수의 가치를 계산하고, 탐색 깊이로 난이도를 조절한다.
(계획서 5.2)
"""

DIFFICULTY_DEPTH = {"easy": 1, "normal": 2, "hard": 4}


class OmokAI:
    """탐색 기반 오목 AI."""

    def __init__(self, difficulty: str = "normal") -> None:
        self.depth = DIFFICULTY_DEPTH.get(difficulty, 2)

    def best_move(self, board) -> tuple[int, int]:
        """현재 판에서 최선의 착수 좌표 (row, col)를 반환한다."""
        # TODO: minimax(board, self.depth, alpha=-inf, beta=+inf, maximizing=True)
        raise NotImplementedError

    def _minimax(self, board, depth, alpha, beta, maximizing):
        # TODO: 알파-베타 가지치기 탐색
        raise NotImplementedError

    def _evaluate(self, board) -> int:
        """평가 함수: 연결 형태에 점수를 매겨 판세를 수치화한다."""
        # TODO: 열린 2/3/4, 5목 등 패턴 점수화
        raise NotImplementedError
