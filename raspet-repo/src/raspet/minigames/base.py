"""미니게임 공통 인터페이스.

모든 미니게임은 이 클래스를 상속해 동일한 방식으로 실행/보상 처리된다.
"""
from abc import ABC, abstractmethod


class MiniGame(ABC):
    """미니게임 베이스 클래스."""

    name: str = "minigame"

    @abstractmethod
    def play(self) -> int:
        """게임을 실행하고 획득 재화(점수)를 반환한다."""
        ...
