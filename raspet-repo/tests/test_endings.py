"""엔딩 분기 테스트."""
from raspet.character.character import Character
from raspet.character.endings import determine_ending


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
