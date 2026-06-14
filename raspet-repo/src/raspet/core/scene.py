"""씬(상태) 머신.

메뉴 → 육성 → 미니게임 → 상점 → 엔딩 사이의 화면 전환을 관리한다.
각 씬은 매 프레임 handle_input → update → render 순으로 호출되며,
app(GameLoop)을 통해 ctx·캐릭터·상점·씬 전환에 접근한다.
"""
from abc import ABC, abstractmethod


class Scene(ABC):
    """모든 화면(씬)의 공통 인터페이스."""

    @abstractmethod
    def handle_input(self, actions: set, app) -> None:
        """이번 프레임의 행동 집합(actions)을 처리한다."""
        ...

    def update(self, dt: float, app) -> None:
        """시간 경과 갱신 (필요한 씬만 구현)."""
        ...

    @abstractmethod
    def render(self, ctx) -> None:
        """현재 화면을 ctx에 그린다."""
        ...


class SceneManager:
    """현재 씬을 보관하고 전환한다."""

    def __init__(self) -> None:
        self.current: Scene | None = None

    def switch_to(self, scene: Scene) -> None:
        self.current = scene
