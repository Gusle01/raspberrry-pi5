"""저장/불러오기 (SQLite 또는 JSON).

캐릭터 능력치·재화·아이템·마지막 플레이 시각을 저장해
전원을 꺼도 진행 상황이 유지되도록 한다. (계획서 4.1.2 / 기술스택)

백엔드는 config.SAVE_BACKEND("json" | "sqlite")로 선택한다.
저장 포맷(공통): {"saved_at": <epoch>, "character": {<필드>...}}
"""
import json
import sqlite3
import time
from pathlib import Path

from .. import config
from ..character.character import Character


def _build_payload(character: Character) -> dict:
    return {"saved_at": time.time(), "character": character.to_dict()}


def save_game(character: Character) -> None:
    """현재 게임 상태를 저장한다 (마지막 플레이 시각 포함)."""
    payload = _build_payload(character)
    if config.SAVE_BACKEND == "sqlite":
        _save_sqlite(payload)
    else:
        _save_json(payload)


def load_game() -> dict | None:
    """저장된 상태를 {"saved_at", "character"} dict로 반환한다. 없으면 None."""
    if config.SAVE_BACKEND == "sqlite":
        return _load_sqlite()
    return _load_json()


def load_character() -> tuple[Character, float]:
    """캐릭터와 마지막 저장 시각을 복원한다. 저장이 없으면 새 캐릭터를 만든다."""
    data = load_game()
    if not data:
        return Character(currency=config.START_CURRENCY), time.time()
    character = Character.from_dict(data.get("character", {}))
    return character, float(data.get("saved_at", time.time()))


# ── JSON 백엔드 ──────────────────────────────────────────
def _save_json(payload: dict) -> None:
    path = Path(config.SAVE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8")


def _load_json() -> dict | None:
    path = Path(config.SAVE_PATH)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


# ── SQLite 백엔드 ────────────────────────────────────────
def _sqlite_connect() -> sqlite3.Connection:
    path = Path(config.SAVE_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE IF NOT EXISTS save "
                 "(id INTEGER PRIMARY KEY CHECK (id = 1), data TEXT)")
    return conn


def _save_sqlite(payload: dict) -> None:
    blob = json.dumps(payload, ensure_ascii=False)
    with _sqlite_connect() as conn:
        conn.execute("INSERT INTO save (id, data) VALUES (1, ?) "
                     "ON CONFLICT(id) DO UPDATE SET data = excluded.data", (blob,))


def _load_sqlite() -> dict | None:
    with _sqlite_connect() as conn:
        row = conn.execute("SELECT data FROM save WHERE id = 1").fetchone()
    if not row:
        return None
    try:
        return json.loads(row[0])
    except json.JSONDecodeError:
        return None
