"""저장/불러오기 테스트 (JSON · SQLite 양쪽)."""
import pytest

from raspet.character.character import Character
from raspet.storage import save
from raspet import config


@pytest.fixture
def tmp_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SAVE_PATH", str(tmp_path / "save.json"))
    monkeypatch.setattr(config, "SAVE_DB_PATH", str(tmp_path / "save.db"))
    return tmp_path


@pytest.mark.parametrize("backend", ["json", "sqlite"])
def test_save_load_roundtrip(tmp_paths, monkeypatch, backend):
    monkeypatch.setattr(config, "SAVE_BACKEND", backend)
    ch = Character(name="별이", intellect=33, currency=120, inventory=["hat"], xp=275)
    save.save_game(ch)
    data = save.load_game()
    assert data is not None
    assert "saved_at" in data
    restored = Character.from_dict(data["character"])
    assert restored == ch
    # XP/레벨이 재시작 후에도 유지된다
    assert restored.xp == 275
    assert restored.level() == ch.level()


def test_load_missing_returns_none(tmp_paths, monkeypatch):
    monkeypatch.setattr(config, "SAVE_BACKEND", "json")
    assert save.load_game() is None


def test_load_character_defaults_when_empty(tmp_paths, monkeypatch):
    monkeypatch.setattr(config, "SAVE_BACKEND", "json")
    ch, ts = save.load_character()
    assert ch.currency == config.START_CURRENCY
    assert ts > 0
