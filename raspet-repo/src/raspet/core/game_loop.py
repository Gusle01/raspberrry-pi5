"""메인 게임 루프 (Pygame 기반).

입력 처리 → 상태 갱신 → 렌더 → 출력(창/OLED) → FPS 제한을 반복한다.
씬 전환은 SceneManager가, 입출력/하드웨어는 GameContext가 담당한다.
"""
import time

from .scene import SceneManager
from .scenes import MenuScene
from ..shop.shop import Shop
from ..character import needs
from ..storage import save


class GameLoop:
    """게임 전체를 구동하는 메인 루프 겸 앱 상태 컨테이너."""

    def __init__(self, ctx, character, last_saved_ts=None) -> None:
        self.ctx = ctx
        self.ctx.app = self                # 씬에서 ctx.app 으로 접근
        self.character = character
        self.shop = Shop()
        self.scenes = SceneManager()
        self.running = True

        # 마지막 플레이 이후 경과 시간만큼 돌봄 상태 감소 (다마고치 요소)
        if last_saved_ts is not None:
            needs.apply_time_decay(character, last_saved_ts, time.time())

        self.scenes.switch_to(MenuScene())

    def switch(self, scene) -> None:
        self.scenes.switch_to(scene)

    def run(self) -> None:
        """메인 루프."""
        ctx = self.ctx
        while self.running and ctx.running:
            actions = ctx.poll()
            dt = ctx.tick()
            scene = self.scenes.current
            scene.handle_input(actions, self)
            scene.update(dt, self)
            scene.render(ctx)
            ctx.present()
        self._on_exit()

    def _on_exit(self) -> None:
        """종료 시 진행 상황을 저장한다."""
        save.save_game(self.character)

    def stop(self) -> None:
        self.running = False
