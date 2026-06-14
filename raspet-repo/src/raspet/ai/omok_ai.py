"""오목 대전 AI — Minimax + 알파-베타 가지치기.

학습 모델 없이 탐색 기반으로 구현한다. 돌의 연결 형태(열린 2·열린 3·4 등)에
점수를 부여하는 평가 함수로 수의 가치를 계산하고, 탐색 깊이로 난이도를 조절한다.
(계획서 5.2)

좌표 규약: board[row][col], 0=빈칸. 돌 색은 정수로 표현하며
어떤 정수가 AI/상대인지는 생성 시 주입받는다(기본 AI=2, 상대=1).
"""
from .. import config

EMPTY = 0

# 난이도 → 탐색 깊이
# 난이도별 (탐색 깊이, 분기당 후보 수 상한)
# Pi 5에서도 한 수가 수 초 내에 끝나도록 후보 수를 제한한다.
DIFFICULTY_SETTINGS = {
    "easy": (1, 16),
    "normal": (2, 14),
    "hard": (3, 10),
}

# 길이 5 윈도우 안의 같은 색 돌 개수별 점수(나머지는 빈칸일 때)
_WINDOW_SCORE = {0: 0, 1: 1, 2: 10, 3: 100, 4: 1000, 5: 100_000}

# 평가/탐색에서 5목을 사실상 무한대로 취급하기 위한 경계값
WIN_SCORE = 1_000_000

# 4방향(가로, 세로, ↘, ↗) 단위 벡터
_DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


class OmokAI:
    """탐색 기반 오목 AI."""

    def __init__(self, difficulty: str = "normal",
                 ai_stone: int = 2, human_stone: int = 1) -> None:
        self.depth, self.max_candidates = DIFFICULTY_SETTINGS.get(
            difficulty, DIFFICULTY_SETTINGS["normal"])
        self.ai_stone = ai_stone
        self.human_stone = human_stone
        self.win_length = config.OMOK_WIN_LENGTH

    # ── 공개 API ────────────────────────────────────────
    def best_move(self, board) -> tuple[int, int]:
        """현재 판에서 최선의 착수 좌표 (row, col)를 반환한다."""
        size = len(board)
        moves = self._candidate_moves(board)
        if not moves:
            center = size // 2
            return (center, center)

        # 1) 즉시 이길 수 있으면 바로 둔다.
        for r, c in moves:
            board[r][c] = self.ai_stone
            won = self._is_win_at(board, r, c, self.ai_stone)
            board[r][c] = EMPTY
            if won:
                return (r, c)

        # 2) 상대의 즉시 승리는 반드시 막는다.
        for r, c in moves:
            board[r][c] = self.human_stone
            threat = self._is_win_at(board, r, c, self.human_stone)
            board[r][c] = EMPTY
            if threat:
                return (r, c)

        # 3) 알파-베타 탐색 (관련도 높은 후보부터, 상위 N개만)
        ordered = self._ordered_candidates(board, self.ai_stone, self.max_candidates)
        best_move = ordered[0]
        best_score = -WIN_SCORE - 1
        alpha, beta = -WIN_SCORE - 1, WIN_SCORE + 1
        for r, c in ordered:
            board[r][c] = self.ai_stone
            score = self._minimax(board, self.depth - 1, alpha, beta, False)
            board[r][c] = EMPTY
            if score > best_score:
                best_score = score
                best_move = (r, c)
            alpha = max(alpha, best_score)
        return best_move

    # ── 탐색 ────────────────────────────────────────────
    def _minimax(self, board, depth, alpha, beta, maximizing) -> int:
        """알파-베타 가지치기 미니맥스. 평가 점수를 반환한다.

        성능을 위해 단말에서만 전체 평가를 수행하고, 내부 노드에서는 착수 직후
        5목 완성 여부만 즉시 검사해 가지를 끊는다.
        """
        if depth == 0:
            return self._evaluate(board)

        stone = self.ai_stone if maximizing else self.human_stone
        moves = self._ordered_candidates(board, stone, self.max_candidates)
        if not moves:
            return self._evaluate(board)

        if maximizing:
            value = -WIN_SCORE - 1
            for r, c in moves:
                board[r][c] = self.ai_stone
                if self._is_win_at(board, r, c, self.ai_stone):
                    board[r][c] = EMPTY
                    return WIN_SCORE          # AI 즉시 승리 → 더 볼 필요 없음
                value = max(value, self._minimax(board, depth - 1, alpha, beta, False))
                board[r][c] = EMPTY
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = WIN_SCORE + 1
            for r, c in moves:
                board[r][c] = self.human_stone
                if self._is_win_at(board, r, c, self.human_stone):
                    board[r][c] = EMPTY
                    return -WIN_SCORE         # 상대 즉시 승리
                value = min(value, self._minimax(board, depth - 1, alpha, beta, True))
                board[r][c] = EMPTY
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return value

    # ── 평가 함수 ───────────────────────────────────────
    def _evaluate(self, board) -> int:
        """판세를 수치화한다. (AI 유리 → 양수, 상대 유리 → 음수)

        모든 길이 5 윈도우를 훑어, 한 색의 돌만 들어있는 윈도우에 점수를 부여한다.
        상대 위협은 약간 더 크게 반영해 방어적으로 둔다.
        """
        size = len(board)
        win = self.win_length
        ai, human = self.ai_stone, self.human_stone
        total = 0

        for r in range(size):
            for c in range(size):
                for dr, dc in _DIRECTIONS:
                    er, ec = r + dr * (win - 1), c + dc * (win - 1)
                    if not (0 <= er < size and 0 <= ec < size):
                        continue
                    ai_count = human_count = 0
                    for k in range(win):
                        v = board[r + dr * k][c + dc * k]
                        if v == ai:
                            ai_count += 1
                        elif v == human:
                            human_count += 1
                    if ai_count and human_count:
                        continue  # 두 색이 섞인 윈도우는 무의미
                    if ai_count:
                        if ai_count >= win:
                            total += WIN_SCORE
                        else:
                            total += _WINDOW_SCORE[ai_count]
                    elif human_count:
                        if human_count >= win:
                            total -= WIN_SCORE
                        else:
                            total -= int(_WINDOW_SCORE[human_count] * 1.1)
        return total

    # ── 보조 ────────────────────────────────────────────
    def _candidate_moves(self, board) -> list[tuple[int, int]]:
        """기존 돌 주변(체비쇼프 거리 ≤ 2)의 빈칸만 후보로 추린다.

        빈 칸 전체를 보지 않아 분기 수를 크게 줄인다. 돌이 하나도 없으면 빈 목록.
        """
        size = len(board)
        candidates = set()
        has_stone = False
        for r in range(size):
            for c in range(size):
                if board[r][c] == EMPTY:
                    continue
                has_stone = True
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == EMPTY:
                            candidates.add((nr, nc))
        if not has_stone:
            return []
        return sorted(candidates)

    def _ordered_candidates(self, board, stone, limit) -> list[tuple[int, int]]:
        """후보 수를 관련도 순으로 정렬해 상위 `limit`개만 돌려준다.

        관련도 = 그 칸에 두었을 때의 공격 가치 + 상대가 두었을 때의 방어 가치.
        가지치기 효율을 높이고 분기 수를 제한해 Pi에서도 빠르게 동작하게 한다.
        """
        other = self.human_stone if stone == self.ai_stone else self.ai_stone
        scored = []
        for r, c in self._candidate_moves(board):
            relevance = (self._move_relevance(board, r, c, stone)
                         + self._move_relevance(board, r, c, other))
            scored.append((relevance, r, c))
        scored.sort(reverse=True)
        return [(r, c) for _, r, c in scored[:limit]]

    def _move_relevance(self, board, r, c, stone) -> int:
        """(r, c)에 stone을 둘 때 그 점을 지나는 4방향 연결 가치의 근사값.

        판 전체가 아니라 해당 칸을 지나는 선만 보므로 정렬용으로 충분히 가볍다.
        """
        size = len(board)
        total = 0
        for dr, dc in _DIRECTIONS:
            count = 1
            for sign in (1, -1):
                nr, nc = r + dr * sign, c + dc * sign
                while 0 <= nr < size and 0 <= nc < size and board[nr][nc] == stone:
                    count += 1
                    nr += dr * sign
                    nc += dc * sign
            total += _WINDOW_SCORE[min(count, self.win_length)]
        return total

    def _is_win_at(self, board, r, c, stone) -> bool:
        """(r, c)에 놓인 stone이 win_length 이상 연속을 만드는지 검사한다."""
        size = len(board)
        win = self.win_length
        for dr, dc in _DIRECTIONS:
            count = 1
            for sign in (1, -1):
                nr, nc = r + dr * sign, c + dc * sign
                while 0 <= nr < size and 0 <= nc < size and board[nr][nc] == stone:
                    count += 1
                    nr += dr * sign
                    nc += dc * sign
            if count >= win:
                return True
        return False
