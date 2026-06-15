"""초음파 점프 게임 (제안).

초음파 센서로 손의 높이(거리)를 읽어 캐릭터를 위아래로 움직여, 다가오는 위·아래
장애물 사이의 구멍을 통과한다(플래피버드식). (계획서 4.2.3)

물리/충돌 로직(JumpEngine)은 순수 파이썬이라 하드웨어 없이 테스트 가능.
UltrasonicJump(MiniGame)가 ctx로 센서 입력과 렌더를 붙인다.
"""
import random

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


class Obstacle:
    """위·아래 파이프 한 쌍. gap_lo~gap_hi(정규화 0=바닥~1=천장)가 통과 구멍이다.

    아래 파이프는 0~gap_lo, 위 파이프는 gap_hi~1을 막으므로 둘의 길이(gap_lo, 1-gap_hi)는
    구멍 위치에 따라 매번 달라진다.
    """

    __slots__ = ("x", "gap_lo", "gap_hi")

    def __init__(self, x: float, gap_lo: float, gap_hi: float) -> None:
        self.x = x
        self.gap_lo = gap_lo
        self.gap_hi = gap_hi


class JumpEngine:
    """위·아래 장애물 구멍 통과 로직. 좌표는 0.0~1.0 정규화 공간을 쓴다."""

    PLAYER_X = 0.2          # 플레이어의 고정 x 위치
    OBSTACLE_SPEED = 0.6    # 초당 이동(좌측으로)
    HIT_MARGIN = 0.06       # 이 x 거리 안일 때 충돌 판정
    PLAYER_HALF = 0.07      # 플레이어 반높이 — 몸 전체가 구멍 안이어야 통과
    EDGE_MARGIN = 0.08      # 구멍이 천장/바닥에 너무 붙지 않게(양쪽 파이프 최소 길이 보장)

    def __init__(self, rng=None) -> None:
        self.player_height = 0.5     # 시작은 화면 가운데
        self.obstacles = []
        self.alive = True
        self.passed = 0
        self._spawn_timer = 0.0
        self._rng = rng or random.Random()

    def set_player_height(self, h: float) -> None:
        self.player_height = max(0.0, min(1.0, h))

    def _spawn(self) -> None:
        """위·아래 파이프 한 쌍을 화면 오른쪽 끝에 만든다. 구멍 크기·위치는 무작위지만
        항상 통과 가능(>= 플레이어 높이 + 여유)하고 양쪽 파이프가 모두 남도록 보장한다."""
        gap = self._rng.uniform(config.JUMP_GAP_MIN, config.JUMP_GAP_MAX)
        half = gap / 2.0
        center = self._rng.uniform(half + self.EDGE_MARGIN, 1.0 - half - self.EDGE_MARGIN)
        self.obstacles.append(Obstacle(1.0, center - half, center + half))

    def step(self, dt: float) -> bool:
        """dt(초)만큼 진행. 살아있으면 True."""
        if not self.alive:
            return False
        self._spawn_timer += dt * 1000.0
        if self._spawn_timer >= config.JUMP_OBSTACLE_INTERVAL_MS:
            self._spawn_timer = 0.0
            self._spawn()

        ph = self.player_height
        survived = []
        for ob in self.obstacles:
            ob.x -= self.OBSTACLE_SPEED * dt
            # 플레이어 x를 지나는 순간, 몸 전체가 구멍 안이 아니면 충돌.
            if abs(ob.x - self.PLAYER_X) <= self.HIT_MARGIN:
                if (ph - self.PLAYER_HALF < ob.gap_lo
                        or ph + self.PLAYER_HALF > ob.gap_hi):
                    self.alive = False
                    return False
            if ob.x < -self.HIT_MARGIN:
                self.passed += 1     # 화면 밖으로 무사 통과
            else:
                survived.append(ob)
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
        top, bot = 1, h - 1                 # 놀이 영역 세로 범위(px)
        span = bot - top
        ctx.clear()

        def y_of(norm):                     # 정규화 높이(0=바닥,1=천장) → 픽셀 y
            return int(bot - norm * span)

        # 장애물: 위 파이프(천장~gap_hi) + 아래 파이프(gap_lo~바닥). 둘 사이가 통과 구멍.
        pw = 5
        for ob in e.obstacles:
            ox = int(ob.x * w)
            gap_hi_y = y_of(ob.gap_hi)
            gap_lo_y = y_of(ob.gap_lo)
            ctx.rect(ox, top, pw, max(0, gap_hi_y - top), config.COLOR_WARN)       # 위 파이프
            ctx.rect(ox, gap_lo_y, pw, max(0, bot - gap_lo_y), config.COLOR_WARN)  # 아래 파이프
        # 플레이어(가운데를 player_height에 맞춤)
        px = int(e.PLAYER_X * w)
        py = y_of(e.player_height)
        ctx.rect(px - 3, py - 3, 6, 6, config.COLOR_ACCENT)
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
