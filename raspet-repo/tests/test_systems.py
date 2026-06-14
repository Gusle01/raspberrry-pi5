"""신규 게임 시스템 테스트 — 무드 · 시간대 · 랜덤 이벤트 · 업적 · 스프라이트."""
from raspet.character.character import Character
from raspet.character.mood import compute_mood
from raspet.core import daytime
from raspet import events, achievements, config


# ── 무드 ─────────────────────────────────────────────────
def test_mood_priority_sick_over_hungry():
    ch = Character(health=10, fullness=0)      # 둘 다 나쁘면 아픔이 우선
    assert compute_mood(ch) == "sick"


def test_mood_states():
    assert compute_mood(Character(health=100, fullness=5)) == "hungry"
    assert compute_mood(Character(cleanliness=5)) == "dirty"
    assert compute_mood(Character(stress=90)) == "stressed"
    assert compute_mood(Character(happiness=95)) == "happy"
    assert compute_mood(Character(happiness=10)) == "sad"
    assert compute_mood(Character(happiness=50)) == "neutral"


# ── 시간대 ───────────────────────────────────────────────
def test_period_for_hour():
    assert daytime.period_for_hour(8) == "morning"
    assert daytime.period_for_hour(14) == "day"
    assert daytime.period_for_hour(19) == "evening"
    assert daytime.period_for_hour(2) == "night"
    assert daytime.period_for_hour(23) == "night"


def test_tint_and_greeting_for_all_periods():
    for p in ("morning", "day", "evening", "night"):
        assert len(daytime.tint(p)) == 3
        assert isinstance(daytime.greeting(p), str)


# ── 랜덤 이벤트 ──────────────────────────────────────────
class _FakeRNG:
    def __init__(self, rand_value=0.0, pick=0):
        self._rand = rand_value
        self._pick = pick

    def random(self):
        return self._rand

    def choices(self, pool, weights, k=1):
        return [pool[self._pick]]


def test_force_event_applies_effect():
    ch = Character(currency=0)
    ev = events.force_event(ch, _FakeRNG(pick=0))   # found_coin: +10 재화
    assert ev["id"] == "found_coin"
    assert ch.currency == 10


def test_maybe_trigger_respects_chance():
    ch = Character(currency=0)
    assert events.maybe_trigger(ch, _FakeRNG(rand_value=0.99)) is None   # 발생 안 함
    assert ch.currency == 0
    ev = events.maybe_trigger(ch, _FakeRNG(rand_value=0.0, pick=0))      # 발생
    assert ev is not None


# ── 업적 ─────────────────────────────────────────────────
def test_achievement_unlock_and_idempotent():
    ch = Character(games_played=1)
    newly = achievements.check_and_unlock(ch)
    ids = {a["id"] for a in newly}
    assert "first_game" in ids
    assert "first_game" in ch.achievements
    # 두 번째 호출에선 같은 업적이 다시 잡히지 않는다
    assert all(a["id"] != "first_game" for a in achievements.check_and_unlock(ch))


def test_achievement_stat_total():
    ch = Character(strength=50, intellect=50, charm=50, sensitivity=50)  # 합 200
    ids = {a["id"] for a in achievements.check_and_unlock(ch)}
    assert "all_rounder" in ids


def test_all_with_status():
    ch = Character()
    rows = achievements.all_with_status(ch)
    assert len(rows) == len(config.ACHIEVEMENTS)
    assert all(owned is False for _, owned in rows)


# ── 스프라이트 렌더 (충돌 없이 그려지는지) ───────────────
def test_sprite_renders_all_stages_and_moods():
    from raspet.core.context import GameContext
    from raspet.core.sprite import draw_pet
    ctx = GameContext(hardware={}, headless=True, script=[set()])
    moods = [Character(health=10), Character(fullness=5), Character(happiness=95),
             Character(happiness=10), Character(stress=90), Character()]
    for stage in range(4):
        for ch in moods:
            ch.stage = stage
            draw_pet(ctx, ch, 64, 32)      # 예외 없이 그려져야 한다
    ctx.present()
