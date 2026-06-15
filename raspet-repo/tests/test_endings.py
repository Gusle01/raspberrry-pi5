"""엔딩 분기 테스트."""
from raspet.character.character import Character
from raspet.character.endings import determine_ending, check_forced_ending
from raspet import config


def test_scholar_ending():
    ch = Character(intellect=80)
    assert determine_ending(ch)["id"] == "scholar"


def test_artist_ending():
    ch = Character(intellect=10, sensitivity=85)
    assert determine_ending(ch)["id"] == "artist"


def test_fallback_ending_for_low_stats():
    ch = Character(strength=5, intellect=5, charm=5, sensitivity=5)
    assert determine_ending(ch)["id"] == "ordinary"


def test_priority_order():
    # 지력과 매력이 모두 높으면 우선순위가 앞선 학자 채택
    ch = Character(intellect=90, charm=90)
    assert determine_ending(ch)["id"] == "scholar"


# ── 방치/스트레스 강제 엔딩 ──────────────────────────────
def test_no_forced_ending_when_healthy():
    assert check_forced_ending(Character()) is None


def test_stress_max_forces_runaway():
    ch = Character(stress=config.STAT_MAX)
    assert check_forced_ending(ch)["id"] == "runaway"


def test_neglect_endings_per_need():
    n = config.NEGLECT_ENDING_DAYS
    for need, ending_id in [("fullness", "thief"), ("cleanliness", "sick"),
                            ("happiness", "wanderer")]:
        ch = Character(zero_days={need: n})
        assert check_forced_ending(ch)["id"] == ending_id


def test_neglect_below_threshold_no_ending():
    ch = Character(zero_days={"fullness": config.NEGLECT_ENDING_DAYS - 1})
    assert check_forced_ending(ch) is None
