"""저장/불러오기 (SQLite 또는 JSON).

캐릭터 능력치·재화·아이템·마지막 플레이 시각을 저장해
전원을 꺼도 진행 상황이 유지되도록 한다. (계획서 4.1.2 / 기술스택)
"""
import json
import time
from pathlib import Path

from .. import config


def save_game(character) -> None:
    """현재 게임 상태를 저장한다 (마지막 플레이 시각 포함)."""
    data = {
        "saved_at": time.time(),
        # TODO: dataclasses.asdict(character) 등으로 직렬화
    }
    if config.SAVE_BACKEND == "json":
        path = Path(config.SAVE_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        # TODO: SQLite 저장
        raise NotImplementedError


def load_game():
    """저장된 게임 상태를 불러온다. 없으면 None."""
    if config.SAVE_BACKEND == "json":
        path = Path(config.SAVE_PATH)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    # TODO: SQLite 불러오기
    raise NotImplementedError
