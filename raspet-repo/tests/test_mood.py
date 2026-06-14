"""감정 표현(무드) 테스트 — 데이터 규칙 기반 매핑 검증."""
from raspet.character.character import Character
from raspet.character import mood
from raspet import config


def _ch(**kw) -> Character:
    """건강한 기본값에서 시작해 일부만 바꾼 캐릭터(다른 규칙 오발 방지)."""
    base = dict(health=80, fullness=80, cleanliness=80, stress=10, happiness=50)
    base.update(kw)
    return Character(**base)


# period는 졸림 규칙에만 쓰이므로, 졸림 외 테스트는 낮(day)으로 고정한다.
def m(ch) -> str:
    return mood.compute_mood(ch, period="day")


def test_mood_labels_cover_all_rules_and_excited():
    for rule in config.MOODS:
        assert rule["id"] in mood.MOOD_LABELS
    assert mood.MOOD_LABELS["excited"] == "신나요!"


def test_sick_has_top_priority():
    # 배고프고 지저분하고 아파도 → 아픔이 우선
    ch = _ch(health=10, fullness=5, cleanliness=5)
    assert m(ch) == "sick"


def test_hungry_over_dirty():
    ch = _ch(fullness=10, cleanliness=10)
    assert m(ch) == "hungry"


def test_dirty():
    assert m(_ch(cleanliness=10)) == "dirty"


def test_stressed():
    assert m(_ch(stress=80)) == "stressed"


def test_lonely_is_neglect_not_plain_sadness():
    # 외로움: 행복 바닥 + 배도 곯음(방치). sad보다 우선.
    assert m(_ch(happiness=10, fullness=40)) == "lonely"
    # 배는 충분한데 행복만 낮으면 단순 우울(sad)
    assert m(_ch(happiness=25, fullness=80)) == "sad"


def test_happy():
    assert m(_ch(happiness=85)) == "happy"


def test_neutral_default():
    assert m(_ch()) == "neutral"


def test_sleepy_only_at_night_and_low_priority():
    ch = _ch()                       # 평범한 상태
    assert mood.compute_mood(ch, period="night") == "sleepy"
    assert mood.compute_mood(ch, period="day") == "neutral"
    # 졸림은 happy/sad보다 우선순위가 낮다 → 밤이어도 행복하면 happy
    assert mood.compute_mood(_ch(happiness=85), period="night") == "happy"


def test_thresholds_come_from_config():
    # config 임계값을 바꾸면 결과가 따라 바뀐다(코드에 박혀있지 않음).
    ch = _ch(stress=60)
    assert m(ch) == "neutral"
    original = config.MOODS
    patched = [dict(r, when=[("stress", ">=", 55)]) if r["id"] == "stressed" else r
               for r in original]
    config.MOODS = patched
    try:
        assert m(ch) == "stressed"
    finally:
        config.MOODS = original


def test_compute_mood_resolves_period_when_omitted():
    # period를 생략해도 예외 없이 동작한다(현재 시각으로 계산).
    assert mood.compute_mood(_ch()) in mood.MOOD_LABELS
