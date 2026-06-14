"""조이스틱 미니게임 (제안): 스네이크.

단순 흑백·저해상도 화면에 적합. (계획서 4.2.4)
게임 로직(SnakeEngine)은 순수 파이썬이라 하드웨어 없이 테스트할 수 있고,
Snake(MiniGame)가 ctx로 입력/렌더를 붙인다.
"""
import random
from collections import deque

from .base import MiniGame
from .. import config

_OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
_DELTA = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


class SnakeEngine:
    """격자 위 스네이크의 순수 게임 로직."""

    def __init__(self, cols=None, rows=None, rng=None) -> None:
        self.cols = cols or config.SNAKE_COLS
        self.rows = rows or config.SNAKE_ROWS
        self.rng = rng or random.Random()
        cx, cy = self.cols // 2, self.rows // 2
        self.snake = deque([(cx, cy), (cx - 1, cy)])  # 머리가 왼쪽 끝(index 0)
        self.direction = "right"
        self.alive = True
        self.score = 0
        self.food = self._spawn_food()

    def _spawn_food(self):
        free = [(x, y) for x in range(self.cols) for y in range(self.rows)
                if (x, y) not in self.snake]
        if not free:
            return None
        return self.rng.choice(free)

    def set_direction(self, d: str) -> None:
        """방향 전환(역방향은 무시)."""
        if d in _DELTA and d != _OPPOSITE.get(self.direction):
            self.direction = d

    def step(self) -> bool:
        """한 칸 전진한다. 살아있으면 True."""
        if not self.alive:
            return False
        dx, dy = _DELTA[self.direction]
        hx, hy = self.snake[0]
        nx, ny = hx + dx, hy + dy
        # 벽 충돌
        if not (0 <= nx < self.cols and 0 <= ny < self.rows):
            self.alive = False
            return False
        # 자기 몸 충돌 (꼬리 끝은 이번에 빠지므로 먹이 없을 때 충돌에서 제외)
        body = self.snake if (nx, ny) == self.food else list(self.snake)[:-1]
        if (nx, ny) in body:
            self.alive = False
            return False
        self.snake.appendleft((nx, ny))
        if (nx, ny) == self.food:
            self.score += 1
            self.food = self._spawn_food()
        else:
            self.snake.pop()
        return True


class Snake(MiniGame):
    name = "스네이크"

    def __init__(self, ctx=None, rng=None) -> None:
        self.ctx = ctx
        self.engine = SnakeEngine(rng=rng)

    def play(self) -> int:
        """스네이크를 플레이하고 먹은 먹이당 보상을 합산해 반환한다."""
        ctx = self.ctx
        if ctx is None:
            return 0
        elapsed_ms = 0.0
        while ctx.running and self.engine.alive:
            for a in ctx.poll():
                if a == "b":
                    return self._reward()
                self.engine.set_direction(a)
            elapsed_ms += ctx.tick() * 1000.0
            if elapsed_ms >= config.SNAKE_TICK_MS:
                elapsed_ms = 0.0
                self.engine.step()
            self._render()
        self._game_over()
        return self._reward()

    def _reward(self) -> int:
        return self.engine.score * config.SNAKE_REWARD_PER_FOOD

    def _render(self) -> None:
        ctx = self.ctx
        e = self.engine
        cw = ctx.width / e.cols
        ch = ctx.height / e.rows
        ctx.clear()
        if e.food:
            fx, fy = e.food
            ctx.rect(fx * cw, fy * ch, cw, ch, config.COLOR_WARN)
        for (x, y) in e.snake:
            ctx.rect(x * cw, y * ch, cw, ch, config.COLOR_ACCENT)
        ctx.text(f"{e.score}", 2, 2, color=config.COLOR_DIM)
        ctx.present()

    def _game_over(self) -> None:
        ctx = self.ctx
        if not ctx.running:
            return
        ctx.clear()
        ctx.text("게임 오버", ctx.width // 2, 22, big=True, center=True)
        ctx.text(f"점수 {self.engine.score}", ctx.width // 2, 44, center=True)
        ctx.present()
        ctx.wait_action({"a", "b"})
