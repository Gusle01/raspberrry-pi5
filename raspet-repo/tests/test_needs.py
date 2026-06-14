"""시간 경과 감소 및 돌봄 행동 테스트."""
from raspet.character.character import Character
from raspet.character import needs
from raspet import config


def test_decay_reduces_needs():
    ch = Character(fullness=100, cleanliness=100)
    # 2시간 경과
    needs.apply_time_decay(ch, last_played_ts=0, now_ts=2 * 3600)
    expected_drop = int(2 * config.NEED_DECAY_PER_HOUR)
    assert ch.fullness == 100 - expected_drop
    assert ch.cleanliness == 100 - expected_drop


def test_no_decay_for_no_elapsed_time():
    ch = Character(fullness=100)
    needs.apply_time_decay(ch, last_played_ts=1000, now_ts=1000)
    assert ch.fullness == 100


def test_long_neglect_hurts_happiness_and_health():
    ch = Character(fullness=0, cleanliness=0, happiness=100, health=100)
    needs.apply_time_decay(ch, last_played_ts=0, now_ts=10 * 3600)
    assert ch.happiness < 100
    assert ch.health < 100


def test_feed_clean_play():
    ch = Character(fullness=10, cleanliness=10, happiness=10, stress=50)
    needs.feed(ch)
    needs.clean(ch)
    needs.play_with(ch)
    assert ch.fullness == 10 + config.FEED_FULLNESS
    assert ch.cleanliness == 10 + config.CLEAN_CLEANLINESS
    assert ch.happiness == 10 + config.FEED_HAPPINESS + config.PLAY_HAPPINESS
    assert ch.stress == 50 - config.PLAY_STRESS_RELIEF
