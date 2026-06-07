"""씬(상태) 머신.

메뉴 → 육성 → 미니게임 → 상점 → 엔딩 사이의 화면 전환을 관리한다.
"""
from abc import ABC, abstractmethod


class Scene(ABC):
    """모든 화면(씬)의 공통 인터페이스."""

    @abstractmethod
    def handle_input(self, event) -> None: ...

    @abstractmethod
    def update(self, dt: float) -> None: ...

    @abstractmethod
    def render(self, surface) -> None: ...


class SceneManager:
    """현재 씬을 보관하고 전환한다."""

    def __init__(self) -> None:
        self.current: Scene | None = None

    def switch_to(self, scene: Scene) -> None:
        self.current = scene
