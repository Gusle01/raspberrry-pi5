"""XP/레벨 진행도 테스트."""
from raspet.character.character import Character
from raspet.character import progression
from raspet import config


def test_level_starts_at_one():
    assert Character().level() == 1
    assert Character().xp == 0


def test_xp_for_level_curve():
    # Lv.1 = 0, 이후 BASE + (L-1)*STEP 누적
    assert progression.xp_for_level(1) == 0
    assert progression.xp_for_level(2) == config.XP_LEVEL_BASE
    assert progression.xp_for_level(3) == (config.XP_LEVEL_BASE
                                           + config.XP_LEVEL_BASE + config.XP_LEVEL_STEP)
    # 단조 증가
    cums = [progression.xp_for_level(l) for l in range(1, config.XP_MAX_LEVEL + 1)]
    assert cums == sorted(cums)
    assert len(set(cums)) == len(cums)


def test_level_for_xp_boundaries():
    assert progression.level_for_xp(0) == 1
    assert progression.level_for_xp(config.XP_LEVEL_BASE - 1) == 1
    assert progression.level_for_xp(config.XP_LEVEL_BASE) == 2


def test_level_capped_at_max():
    huge = Character(xp=10 ** 9)
    assert huge.level() == config.XP_MAX_LEVEL
    into, need, ratio = huge.xp_progress()
    assert (into, need, ratio) == (0, 0, 1.0)


def test_add_xp_reports_levelup():
    ch = Character()
    before, after = ch.add_xp(config.XP_LEVEL_BASE)   # Lv.1 → Lv.2
    assert (before, after) == (1, 2)
    # 같은 레벨 내 추가는 레벨 변화 없음
    b2, a2 = ch.add_xp(1)
    assert b2 == a2 == 2


def test_add_xp_never_negative():
    ch = Character(xp=10)
    ch.add_xp(-100)
    assert ch.xp == 0


def test_xp_progress_ratio_within_unit_interval():
    for xp in (0, 10, 50, 100, 500, 1000):
        into, need, ratio = Character(xp=xp).xp_progress()
        assert 0.0 <= ratio <= 1.0
        if need:
            assert 0 <= into <= need


def test_title_milestones():
    assert progression.title_for_level(1) == config.LEVEL_TITLES[1]
    # 마일스톤 사이 레벨은 직전 마일스톤 타이틀을 쓴다
    assert progression.title_for_level(2) == config.LEVEL_TITLES[1]
    assert progression.title_for_level(config.XP_MAX_LEVEL) == \
        config.LEVEL_TITLES[config.XP_MAX_LEVEL]


def test_xp_independent_from_core_stats_and_stage():
    # XP는 능력치/진화(stage)와 충돌하지 않는 별도 레이어다.
    ch = Character(strength=50, intellect=50, charm=0, sensitivity=0)
    ch.update_stage()
    stage_before = ch.stage
    total_before = ch.stat_total()
    ch.add_xp(500)
    assert ch.stage == stage_before          # XP가 진화를 건드리지 않음
    assert ch.stat_total() == total_before   # 능력치도 그대로
