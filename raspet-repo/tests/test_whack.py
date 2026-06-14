"""두더지 잡기 — 엔진 로직(결정적) + 헤드리스 통합 테스트."""
import random

from raspet.minigames.whack_a_mole import WhackEngine, WhackAMole, ACTION_HOLE, HOLES
from raspet import config


def _mole(ttl=1.0):
    return {"kind": "mole", "age": 0.0, "ttl": ttl}


def _trap(ttl=1.0):
    return {"kind": "trap", "age": 0.0, "ttl": ttl}


def test_action_hole_mapping():
    assert ACTION_HOLE == {"left": 0, "down": 1, "right": 2}
    assert HOLES == 3


def test_hit_scores_and_combo():
    e = WhackEngine()
    e.moles[1] = _mole()
    assert e.whack(1) == "hit"
    assert e.hits == 1 and e.combo == 1
    assert e.coins == config.WHACK_HIT_REWARD
    assert 1 not in e.moles


def test_empty_whack_resets_combo_no_score():
    e = WhackEngine()
    e.moles[0] = _mole(); e.whack(0)         # combo=1, coins=1
    coins = e.coins
    assert e.whack(2) == "empty"             # 빈 구멍
    assert e.combo == 0
    assert e.coins == coins                  # 점수 변화 없음


def test_combo_bonus_after_step():
    e = WhackEngine()
    for _ in range(config.WHACK_COMBO_STEP):  # 연속 5회 명중
        e.moles[0] = _mole()
        e.whack(0)
    assert e.combo == config.WHACK_COMBO_STEP
    assert e.max_combo == config.WHACK_COMBO_STEP
    # 1~4타: +1씩(=STEP-1), 5타: +1+보너스(1) → 합 = (STEP-1) + (1+BONUS)
    expected = (config.WHACK_COMBO_STEP - 1) * config.WHACK_HIT_REWARD \
        + (config.WHACK_HIT_REWARD + config.WHACK_COMBO_BONUS)
    assert e.coins == expected


def test_trap_penalty_and_combo_reset():
    e = WhackEngine()
    e.coins = 10
    e.combo = 3
    e.moles[0] = _trap()
    assert e.whack(0) == "trap"
    assert e.coins == max(0, 10 - config.WHACK_TRAP_PENALTY)
    assert e.combo == 0
    assert e.misses == 1


def test_miss_on_mole_expire():
    e = WhackEngine()
    e.combo = 2
    e._spawn_cd = 10.0                       # 이번 update에서 새 두더지 재등장 차단(만료만 검증)
    e.moles[2] = _mole(ttl=0.5)
    e.update(0.6)                            # 수명 초과 → 놓침
    assert 2 not in e.moles
    assert e.misses == 1 and e.combo == 0


def test_trap_expire_is_safe():
    e = WhackEngine()
    e.coins = 5
    e._spawn_cd = 10.0                       # 재등장 차단
    e.moles[1] = _trap(ttl=0.5)
    e.update(0.6)                            # 함정은 그냥 사라지면 무사
    assert 1 not in e.moles
    assert e.misses == 0 and e.coins == 5


def test_game_over_after_duration():
    e = WhackEngine(duration=1.0)
    e.update(1.1)
    assert e.over is True
    # 종료 후 입력은 점수에 영향 없음
    e.moles[0] = _mole()
    assert e.whack(0) == "empty"
    assert e.hits == 0


def test_double_moles_only_in_late_game():
    e = WhackEngine()
    e.elapsed = config.WHACK_DOUBLE_AFTER_S - 0.1
    assert e._max_active() == 1
    e.elapsed = config.WHACK_DOUBLE_AFTER_S
    assert e._max_active() == 2


def test_traps_only_after_trap_after_s():
    # 함정 시작 전: rng가 어떤 값이어도 두더지(mole)만 등장
    e = WhackEngine()
    e.elapsed = 0.0
    e.rng = random.Random(0)
    for _ in range(10):
        e.moles.clear()
        e._spawn()
        assert all(m["kind"] == "mole" for m in e.moles.values())


def test_trap_can_appear_after_threshold():
    # 함정 시작 후 + 확률 1.0이면 함정이 등장
    e = WhackEngine()
    e.elapsed = config.WHACK_TRAP_AFTER_S
    e.rng = random.Random(0)
    orig = config.WHACK_TRAP_CHANCE
    config.WHACK_TRAP_CHANCE = 1.0
    try:
        e._spawn()
        assert any(m["kind"] == "trap" for m in e.moles.values())
    finally:
        config.WHACK_TRAP_CHANCE = orig


def test_timeout_shrinks_over_time():
    e = WhackEngine(duration=30.0)
    e.elapsed = 0.0
    e._spawn()
    ttl_start = next(iter(e.moles.values()))["ttl"]
    e.moles.clear()
    e.elapsed = 30.0                         # 진행 100%
    e._spawn()
    ttl_end = next(iter(e.moles.values()))["ttl"]
    assert ttl_start > ttl_end
    assert abs(ttl_start - config.WHACK_TIMEOUT_START_S) < 1e-6
    assert abs(ttl_end - config.WHACK_TIMEOUT_END_S) < 1e-6


# ── 헤드리스 통합 (ctx 바인딩·LED·부저 호출이 죽지 않는지) ──
def test_play_headless_returns_int():
    from raspet.core.context import GameContext
    # 모든 버튼을 매 프레임 눌러 등장하는 두더지를 잡는다(20프레임 후 스크립트 소진→종료)
    script = [{"left", "down", "right"}] * 20
    # ctx.quit()은 pygame.quit()을 호출해 다른 테스트에 영향을 주므로 부르지 않는다
    # (기존 테스트 관례와 동일 — 헤드리스 컨텍스트는 그대로 둔다).
    ctx = GameContext(hardware={}, headless=True, script=script)
    reward = WhackAMole(ctx=ctx, rng=random.Random(1)).play()
    assert isinstance(reward, int) and reward >= 0
