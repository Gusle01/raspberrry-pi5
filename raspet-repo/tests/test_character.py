"""캐릭터 능력치/효과/진화/직렬화 테스트."""
from raspet.character.character import Character
from raspet import config


def test_grow_clamps_to_max():
    ch = Character(intellect=config.STAT_MAX - 2)
    gained = ch.grow("intellect", 10)
    assert ch.intellect == config.STAT_MAX
    assert gained == 2


def test_reset_life_keeps_records_resets_progress():
    ch = Character(name="별이", intellect=80, stress=90, fullness=0, day=42,
                   currency=999, xp=500, stage=3,
                   zero_days={"fullness": 5},
                   achievements=["first_game"], best_scores={"두더지 잡기": 30})
    ch.reset_life()
    # 유지: 이름·업적·베스트기록
    assert ch.name == "별이"
    assert ch.achievements == ["first_game"]
    assert ch.best_scores == {"두더지 잡기": 30}
    # 초기화: 능력치·일수·돌봄·진행·재화
    assert ch.day == 0 and ch.zero_days == {}
    assert ch.intellect == 10 and ch.stress == 0 and ch.fullness == 100
    assert ch.xp == 0 and ch.stage == 0
    assert ch.currency == config.START_CURRENCY


def test_grow_stress_penalty():
    low = Character(stress=0, strength=10)
    high = Character(stress=config.STRESS_PENALTY_THRESHOLD, strength=10)
    g_low = low.grow("strength", 10)
    g_high = high.grow("strength", 10)
    assert g_high < g_low            # 스트레스가 높으면 효율 감소


def test_train_adds_stress():
    ch = Character(stress=0)
    ch.train("strength")
    assert ch.stress == config.STRESS_PER_TRAIN


def test_apply_effects_currency_and_clamp():
    ch = Character(currency=10, happiness=95)
    ch.apply_effects({"currency": 5, "happiness": 20, "stress": -5})
    assert ch.currency == 15
    assert ch.happiness == config.STAT_MAX     # 95+20 → 상한
    assert ch.stress == 0                       # 0-5 → 하한


def test_apply_effects_rejects_unknown_key():
    ch = Character()
    import pytest
    with pytest.raises(ValueError):
        ch.apply_effects({"nonexistent": 1})


def test_update_stage_progression():
    ch = Character(strength=0, intellect=0, charm=0, sensitivity=0)
    assert ch.update_stage() == 0
    ch.strength = ch.intellect = ch.charm = ch.sensitivity = 25  # 합 100
    assert ch.update_stage() >= 1


def test_serialize_roundtrip():
    ch = Character(name="테스트", intellect=42, currency=77, inventory=["hat"])
    restored = Character.from_dict(ch.to_dict())
    assert restored == ch


def test_from_dict_ignores_unknown_keys():
    ch = Character.from_dict({"name": "X", "intellect": 5, "garbage": 1})
    assert ch.name == "X" and ch.intellect == 5


def test_best_score_records_only_improvements():
    ch = Character()
    assert ch.best_score("두더지 잡기") == 0
    assert ch.record_score("두더지 잡기", 12) is True      # 첫 기록 → 신기록
    assert ch.best_score("두더지 잡기") == 12
    assert ch.record_score("두더지 잡기", 8) is False      # 더 낮음 → 갱신 안 함
    assert ch.best_score("두더지 잡기") == 12
    assert ch.record_score("두더지 잡기", 20) is True      # 더 높음 → 갱신
    assert ch.best_score("두더지 잡기") == 20


def test_best_scores_survive_roundtrip():
    ch = Character()
    ch.record_score("스네이크", 30)
    restored = Character.from_dict(ch.to_dict())
    assert restored.best_score("스네이크") == 30
