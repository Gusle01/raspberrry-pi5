"""초음파 점프 게임 (제안).

초음파 센서로 손의 높이(거리)를 읽어 캐릭터의 점프 높이를 제어,
다가오는 장애물을 피한다. (계획서 4.2.3)

물리/충돌 로직(JumpEngine)은 순수 파이썬이라 하드웨어 없이 테스트 가능.
UltrasonicJump(MiniGame)가 ctx로 센서 입력과 렌더를 붙인다.
"""
from .base import MiniGame
from .. import config


def height_from_distance(distance_cm: float) -> float:
    """손 거리(cm)를 0.0(바닥)~1.0(최고점) 높이로 매핑한다. 가까울수록 높다."""
    lo, hi = config.JUMP_DISTANCE_MIN_CM, config.JUMP_DISTANCE_MAX_CM
    if distance_cm <= lo:
        return 1.0
    if distance_cm >= hi:
        return 0.0
    return (hi - distance_cm) / (hi - lo)


class JumpEngine:
    """장애물 회피 로직. 좌표는 0.0~1.0 정규화 공간을 쓴다."""

    PLAYER_X = 0.2          # 플레이어의 고정 x 위치
    OBSTACLE_SPEED = 0.6    # 초당 이동(좌측으로)
    OBSTACLE_HEIGHT = 0.4   # 이 높이 이하면 충돌(점프로 넘어야 함)
    HIT_MARGIN = 0.06

    def __init__(self) -> None:
        self.player_height = 0.0
        self.obstacles = []          # 각 원소: x 위치(1.0에서 시작해 감소)
        self.alive = True
        self.passed = 0
        self._spawn_timer = 0.0

    def set_player_height(self, h: float) -> None:
        self.player_height = max(0.0, min(1.0, h))

    def step(self, dt: float) -> bool:
        """dt(초)만큼 진행. 살아있으면 True."""
        if not self.alive:
            return False
        self._spawn_timer += dt * 1000.0
        if self._spawn_timer >= config.JUMP_OBSTACLE_INTERVAL_MS:
            self._spawn_timer = 0.0
            self.obstacles.append(1.0)

        survived = []
        for x in self.obstacles:
            nx = x - self.OBSTACLE_SPEED * dt
            # 플레이어 위치를 지나는 순간 충돌 판정
            if abs(nx - self.PLAYER_X) <= self.HIT_MARGIN:
                if self.player_height < self.OBSTACLE_HEIGHT:
                    self.alive = False
                    return False
            if nx < -self.HIT_MARGIN:
                self.passed += 1     # 화면 밖으로 무사 통과
            else:
                survived.append(nx)
        self.obstacles = survived
        return True


class UltrasonicJump(MiniGame):
    name = "초음파 점프"

    def __init__(self, ctx=None) -> None:
        self.ctx = ctx
        self.engine = JumpEngine()

    def play(self) -> int:
        ctx = self.ctx
        if ctx is None:
            return 0
        while ctx.running and self.engine.alive:
            for a in ctx.poll():
                if a == "b":
                    return self._reward()
            dt = ctx.tick()
            self.engine.set_player_height(height_from_distance(ctx.distance_cm()))
            self.engine.step(dt)
            self._render()
        self._game_over()
        return self._reward()

    def _reward(self) -> int:
        return self.engine.passed * config.JUMP_REWARD_PER_OBSTACLE

    def _render(self) -> None:
        ctx = self.ctx
        e = self.engine
        w, h = ctx.width, ctx.height
        ground = h - 6
        ctx.clear()
        ctx.rect(0, ground, w, 2, config.COLOR_DIM)
        # 플레이어
        py = ground - int(e.player_height * (h - 16)) - 6
        ctx.rect(int(e.PLAYER_X * w), py, 6, 6, config.COLOR_ACCENT)
        # 장애물
        for x in e.obstacles:
            ctx.rect(int(x * w), ground - 6, 4, 6, config.COLOR_WARN)
        ctx.text(f"{e.passed}", 2, 2, color=config.COLOR_DIM)
        ctx.present()

    def _game_over(self) -> None:
        ctx = self.ctx
        if not ctx.running:
            return
        ctx.clear()
        ctx.text("게임 오버", ctx.width // 2, 22, big=True, center=True)
        ctx.text(f"통과 {self.engine.passed}", ctx.width // 2, 44, center=True)
        ctx.present()
        ctx.wait_action({"a", "b"})
