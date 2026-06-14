"""헤드리스 통합 스모크 테스트.

실제 GameContext(헤드리스) + 더미 하드웨어로 게임 루프와 미니게임 루프를
스크립트된 입력으로 돌려, 충돌 없이 동작하고 보상/상태가 갱신되는지 본다.
"""
import random

import pytest

from raspet.core.context import GameContext
from raspet.core.game_loop import GameLoop
from raspet.character.character import Character
from raspet import config


def make_ctx(script):
    return GameContext(hardware={}, headless=True, script=script)


# ── 개별 미니게임 루프 ───────────────────────────────────
def test_snake_loop_runs_headless():
    from raspet.minigames.snake import Snake
    ctx = make_ctx([{"right"}, {"down"}, {"left"}, {"up"}, set(), set()])
    reward = Snake(ctx=ctx, rng=random.Random(0)).play()
    assert isinstance(reward, int) and reward >= 0


def test_jump_loop_runs_headless():
    from raspet.minigames.jump import UltrasonicJump
    ctx = make_ctx([set(), set(), set(), set()])
    reward = UltrasonicJump(ctx=ctx).play()
    assert isinstance(reward, int) and reward >= 0


def test_rps_loop_with_provider():
    from raspet.minigames.rps import RockPaperScissors
    ctx = make_ctx([{"a"}, {"a"}, {"a"}, {"a"}])
    game = RockPaperScissors(ctx=ctx, choice_provider=lambda c: "rock",
                             rng=random.Random(0))
    reward = game.play()
    assert isinstance(reward, int) and reward >= 0


def test_color_hunt_with_detector():
    from raspet.minigames.color_hunt import ColorHunt
    ctx = make_ctx([set() for _ in range(8)])
    game = ColorHunt(ctx=ctx, detector=lambda frame, target: True,
                     rng=random.Random(0))
    reward = game.play()
    assert reward == config.COLOR_HUNT_ROUNDS * config.COLOR_HUNT_REWARD_PER_ROUND


def test_omok_via_launcher_aborts_cleanly():
    """창이 닫히면(스크립트 소진) 오목 런처가 AbortGame을 삼키고 0을 반환한다."""
    from raspet.core.scenes import run_minigame
    ctx = make_ctx([set()])
    reward = run_minigame("오목", ctx)
    assert reward == 0


# ── 전체 게임 루프 ───────────────────────────────────────
def test_full_gameloop_smoke(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SAVE_PATH", str(tmp_path / "save.json"))
    monkeypatch.setattr(config, "SAVE_BACKEND", "json")

    # 타이틀→메뉴→돌보기→먹이→뒤로→미니게임→스네이크 실행→(스크립트 소진으로 종료)
    script = [
        {"a"},          # 타이틀 → 메뉴
        {"a"},          # 메뉴: 돌보기 선택
        {"a"},          # 돌보기: 먹이주기
        {"b"},          # 뒤로 → 메뉴
        {"down"},       # 메뉴: 미니게임으로 이동
        {"a"},          # 미니게임 메뉴 진입
        {"down"}, {"down"},  # 스네이크로 이동
        {"a"},          # 스네이크 실행 (이후 프레임은 스네이크가 소비)
        {"right"}, {"down"}, set(), set(),
    ]
    ctx = make_ctx(script)
    ch = Character(currency=config.START_CURRENCY, fullness=10)
    full_before = ch.fullness
    game = GameLoop(ctx, ch, last_saved_ts=None)
    game.run()                       # 예외 없이 끝나야 한다

    assert ctx.running is False
    assert ch.fullness > full_before               # 먹이주기 반영
    assert ch.games_played == 1                     # 미니게임 1회 집계
    assert (tmp_path / "save.json").exists()        # 종료 시 저장됨
