"""오목 코어 + AI 단위 테스트 (하드웨어 불필요)."""
import pytest

from raspet.minigames.omok import Omok, HUMAN, AI, EMPTY
from raspet.ai.omok_ai import OmokAI, WIN_SCORE


def empty_board(size=15):
    return [[EMPTY] * size for _ in range(size)]


# ── 승리 판정 ────────────────────────────────────────────
def test_win_horizontal():
    g = Omok()
    for c in range(5):
        g.board[7][c] = HUMAN
    assert g.check_win(7, 4)


def test_win_vertical():
    g = Omok()
    for r in range(5):
        g.board[r][3] = AI
    assert g.check_win(4, 3)


def test_win_diagonal():
    g = Omok()
    for i in range(5):
        g.board[i][i] = HUMAN
    assert g.check_win(2, 2)


def test_win_anti_diagonal():
    g = Omok()
    for i in range(5):
        g.board[i][10 - i] = HUMAN
    assert g.check_win(0, 10)


def test_four_in_a_row_is_not_win():
    g = Omok()
    for c in range(4):
        g.board[7][c] = HUMAN
    assert not g.check_win(7, 3)


# ── 보드 조작 ────────────────────────────────────────────
def test_place_and_validation():
    g = Omok()
    g.place(0, 0, HUMAN)
    assert g.board[0][0] == HUMAN
    assert not g.is_valid(0, 0)            # 이미 둔 자리
    with pytest.raises(ValueError):
        g.place(0, 0, AI)
    assert not g.is_valid(-1, 0)           # 판 밖


# ── AI 동작 ──────────────────────────────────────────────
def test_ai_opens_at_center_on_empty_board():
    ai = OmokAI()
    move = ai.best_move(empty_board())
    assert move == (7, 7)


def test_ai_takes_immediate_win():
    """AI 돌 4개가 한 줄 → 5번째에 두어 즉시 이겨야 한다."""
    board = empty_board()
    for c in range(4):
        board[7][c] = AI       # AI=2
    board[0][0] = HUMAN        # 후보 생성을 위해 사람 돌도 하나
    ai = OmokAI(difficulty="easy")
    assert ai.best_move(board) == (7, 4)


def test_ai_blocks_immediate_threat():
    """사람 돌 4개가 한 줄 → AI는 막아야 한다."""
    board = empty_board()
    for c in range(4):
        board[7][c] = HUMAN
    board[0][0] = AI
    ai = OmokAI(difficulty="easy")
    assert ai.best_move(board) == (7, 4)


def test_evaluate_signs():
    """AI 우세 → 양수, 사람 우세 → 음수."""
    ai = OmokAI()
    b = empty_board()
    b[7][7] = b[7][8] = b[7][9] = AI
    assert ai._evaluate(b) > 0
    b2 = empty_board()
    b2[7][7] = b2[7][8] = b2[7][9] = HUMAN
    assert ai._evaluate(b2) < 0


def test_evaluate_detects_five():
    ai = OmokAI()
    b = empty_board()
    for c in range(5):
        b[7][c] = AI
    assert ai._evaluate(b) >= WIN_SCORE


# ── 전체 대국 ────────────────────────────────────────────
def first_empty(board):
    """가장 먼저 비어 있는 칸을 고르는 단순 사람 입력기."""
    for r in range(len(board)):
        for c in range(len(board[r])):
            if board[r][c] == EMPTY:
                return (r, c)
    raise AssertionError("빈 칸이 없는데 입력기가 호출됨")


def test_full_game_terminates_with_valid_result():
    """단순 입력기로 끝까지 두면 유효한 승자/보상이 나오고 반드시 종료한다."""
    from raspet import config

    g = Omok(difficulty="easy", move_provider=first_empty)
    reward = g.play()
    assert g.winner in (HUMAN, AI, EMPTY)
    assert reward in (config.OMOK_WIN_REWARD, config.OMOK_LOSE_REWARD,
                      config.OMOK_DRAW_REWARD)
    # 승자가 정해졌다면 그 돌이 실제로 5목을 이루는지 교차 검증
    if g.winner in (HUMAN, AI):
        assert any(
            g.board[r][c] == g.winner and g.check_win(r, c)
            for r in range(g.size) for c in range(g.size)
        )


def test_play_requires_move_provider():
    g = Omok()
    with pytest.raises(RuntimeError):
        g.play()
