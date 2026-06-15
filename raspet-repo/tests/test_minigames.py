"""미니게임 순수 로직 테스트 (하드웨어 불필요).

오목은 test_omok.py 에서 별도로 다룬다.
"""
import random

import pytest

from raspet.minigames.rps import judge, CHOICES
from raspet.minigames.snake import SnakeEngine
from raspet.minigames.jump import JumpEngine, Obstacle, height_from_distance
from raspet.minigames.color_hunt import color_match, _CV_AVAILABLE
from raspet import config


# ── 가위바위보 ───────────────────────────────────────────
def test_rps_judge_all_cases():
    assert judge("rock", "scissors") == "win"
    assert judge("scissors", "rock") == "lose"
    assert judge("paper", "paper") == "draw"
    for u in CHOICES:
        for c in CHOICES:
            assert judge(u, c) in ("win", "lose", "draw")


# ── 스네이크 ─────────────────────────────────────────────
def test_snake_eats_and_grows():
    e = SnakeEngine(cols=8, rows=8, rng=random.Random(1))
    head = e.snake[0]
    e.food = (head[0] + 1, head[1])      # 머리 바로 오른쪽에 먹이
    e.direction = "right"
    before = len(e.snake)
    e.step()
    assert e.score == 1
    assert len(e.snake) == before + 1


def test_snake_wall_collision():
    e = SnakeEngine(cols=5, rows=5, rng=random.Random(0))
    e.snake.clear()
    e.snake.append((4, 2))               # 오른쪽 벽에 붙임
    e.direction = "right"
    e.food = (0, 0)
    assert e.step() is False
    assert e.alive is False


def test_snake_no_reverse():
    e = SnakeEngine(cols=8, rows=8)
    e.direction = "right"
    e.set_direction("left")              # 역방향 무시
    assert e.direction == "right"


def test_snake_self_collision():
    e = SnakeEngine(cols=8, rows=8, rng=random.Random(2))
    from collections import deque
    # 2x2 고리 모양. 머리(2,2)가 아래로 가면 몸통(2,3)과 충돌한다(꼬리는 (3,2)).
    e.snake = deque([(2, 2), (2, 3), (3, 3), (3, 2)])
    e.direction = "down"                  # (2,2)→(2,3): 몸통과 충돌
    e.food = (7, 7)
    assert e.step() is False
    assert e.alive is False


# ── 초음파 점프 ──────────────────────────────────────────
def test_height_mapping():
    assert height_from_distance(config.JUMP_DISTANCE_MIN_CM - 1) == 1.0
    assert height_from_distance(config.JUMP_DISTANCE_MAX_CM + 1) == 0.0
    mid = height_from_distance(
        (config.JUMP_DISTANCE_MIN_CM + config.JUMP_DISTANCE_MAX_CM) / 2)
    assert 0.0 < mid < 1.0


def test_jump_collision_outside_gap():
    e = JumpEngine()
    e.obstacles = [Obstacle(e.PLAYER_X, 0.4, 0.8)]   # 구멍 0.4~0.8
    e.set_player_height(0.05)             # 바닥 근처 → 구멍 밖(아래 파이프 충돌)
    assert e.step(0.001) is False
    assert e.alive is False


def test_jump_collision_against_top_pipe():
    e = JumpEngine()
    e.obstacles = [Obstacle(e.PLAYER_X, 0.4, 0.8)]
    e.set_player_height(0.98)             # 천장 근처 → 위 파이프 충돌
    assert e.step(0.001) is False
    assert e.alive is False


def test_jump_clears_through_gap():
    e = JumpEngine()
    e.obstacles = [Obstacle(e.PLAYER_X, 0.4, 0.8)]
    e.set_player_height(0.6)              # 구멍 한가운데 → 통과
    assert e.step(0.001) is True
    assert e.alive is True


def test_jump_spawn_gap_is_passable_and_both_pipes_exist():
    e = JumpEngine(rng=random.Random(0))
    for _ in range(80):
        e._spawn()
    for ob in e.obstacles:
        assert 0.0 < ob.gap_lo < ob.gap_hi < 1.0
        # 구멍이 플레이어 전체 높이보다 넉넉히 큼(항상 통과 가능)
        assert (ob.gap_hi - ob.gap_lo) >= 2 * e.PLAYER_HALF
        # 위·아래 파이프가 모두 최소 길이 이상 존재
        assert ob.gap_lo >= e.EDGE_MARGIN - 1e-9
        assert (1.0 - ob.gap_hi) >= e.EDGE_MARGIN - 1e-9


def test_jump_spawn_lengths_vary():
    e = JumpEngine(rng=random.Random(3))
    for _ in range(30):
        e._spawn()
    bottoms = {round(ob.gap_lo, 3) for ob in e.obstacles}
    assert len(bottoms) > 5               # 아래 파이프 길이가 제각각


def test_ultrasonic_dummy_returns_far_distance():
    from raspet.hardware.ultrasonic import DummyUltrasonic
    u = DummyUltrasonic()
    assert u.available is False
    assert u.distance_cm() == float(config.JUMP_DISTANCE_MAX_CM)


def test_ultrasonic_read_never_blocks_game_on_error():
    """센서를 안 꽂아 읽기가 실패해도 게임 루프가 멈추지 않고 안전값으로 폴백한다."""
    from raspet.hardware.ultrasonic import Ultrasonic

    class _Boom:
        @property
        def distance(self):
            raise RuntimeError("에코 없음")

    u = Ultrasonic.__new__(Ultrasonic)   # __init__(실하드웨어) 우회
    u._sensor = _Boom()
    assert u.distance_cm() == float(config.JUMP_DISTANCE_MAX_CM)


# ── 색깔 찾기 ────────────────────────────────────────────
@pytest.mark.skipif(not _CV_AVAILABLE, reason="OpenCV 미설치")
def test_color_match_red():
    import numpy as np
    red = np.zeros((10, 10, 3), dtype=np.uint8)
    red[:, :] = (255, 0, 0)              # RGB 빨강
    name, lower, upper = config.COLOR_HUNT_TARGETS[0]   # 빨강
    assert color_match(red, lower, upper) is True
    blue = np.zeros((10, 10, 3), dtype=np.uint8)
    blue[:, :] = (0, 0, 255)
    assert color_match(blue, lower, upper) is False


def test_color_match_none_frame():
    assert color_match(None, (0, 0, 0), (1, 1, 1)) is False
