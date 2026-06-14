"""두더지 잡기 — LED 3개 + 버튼 3개를 쓰는 반응 미니게임.

구멍(0·1·2)에 두더지가 튀어나오면(해당 LED 점등) 같은 버튼을 제한시간 안에 눌러 잡는다.
- 30초 시간제, 시간이 갈수록 두더지가 빨리 사라지고 등장도 빨라진다.
- 콤보 보너스: 연속 명중 시 추가 점수.
- 함정(누르면 안 되는 LED): 누르면 감점, 그냥 두면 무사.
- 후반에는 동시에 2마리까지 등장(고난도).

게임 로직(WhackEngine)은 순수 파이썬이라 하드웨어 없이 테스트할 수 있고,
WhackAMole(MiniGame)이 ctx로 입력(버튼/키)·출력(LED·부저·화면)을 붙인다.
입력: 실기는 물리 버튼 3개, PC는 ← ↓ → (둘 다 left/down/right 액션으로 들어온다).
"""
import random

from .base import MiniGame
from .. import config

HOLES = 3
# 액션(←↓→ 또는 물리버튼) → 구멍 인덱스
ACTION_HOLE = {"left": 0, "down": 1, "right": 2}


class WhackEngine:
    """두더지 잡기의 순수 게임 로직(시간은 update(dt)로 주입)."""

    def __init__(self, rng=None, duration=None) -> None:
        self.rng = rng or random.Random()
        self.duration = config.WHACK_DURATION_S if duration is None else duration
        self.elapsed = 0.0
        self.coins = 0          # 획득 재화(=점수)
        self.hits = 0
        self.misses = 0
        self.combo = 0
        self.max_combo = 0
        # hole index -> {"kind": "mole"|"trap", "age": float, "ttl": float}
        self.moles: dict[int, dict] = {}
        self._spawn_cd = 0.0    # 다음 등장까지 남은 시간
        self.events: list[tuple[str, int]] = []   # 피드백용(소비됨): (종류, 구멍)
        self.over = False

    # ── 진행도에 따른 보간 ───────────────────────────────
    def _progress(self) -> float:
        return min(1.0, self.elapsed / self.duration) if self.duration else 1.0

    def _lerp(self, start: float, end: float) -> float:
        return start + (end - start) * self._progress()

    def _max_active(self) -> int:
        return 2 if self.elapsed >= config.WHACK_DOUBLE_AFTER_S else 1

    def _spawn(self) -> None:
        free = [i for i in range(HOLES) if i not in self.moles]
        if not free:
            return
        hole = self.rng.choice(free)
        is_trap = (self.elapsed >= config.WHACK_TRAP_AFTER_S
                   and self.rng.random() < config.WHACK_TRAP_CHANCE)
        ttl = self._lerp(config.WHACK_TIMEOUT_START_S, config.WHACK_TIMEOUT_END_S)
        self.moles[hole] = {"kind": "trap" if is_trap else "mole", "age": 0.0, "ttl": ttl}
        self.events.append(("spawn", hole))

    def update(self, dt: float) -> None:
        """dt초만큼 시간을 진행한다(수명 만료·등장 처리)."""
        if self.over:
            return
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.over = True
        # 수명 만료
        for hole in list(self.moles):
            m = self.moles[hole]
            m["age"] += dt
            if m["age"] >= m["ttl"]:
                if m["kind"] == "mole":          # 두더지를 놓침
                    self.misses += 1
                    self.combo = 0
                    self.events.append(("miss", hole))
                del self.moles[hole]             # 함정은 그냥 사라지면 무사
        # 새 두더지 등장
        self._spawn_cd -= dt
        if (not self.over and self._spawn_cd <= 0
                and len(self.moles) < self._max_active()):
            self._spawn()
            self._spawn_cd = self._lerp(config.WHACK_SPAWN_START_S,
                                        config.WHACK_SPAWN_END_S)

    def whack(self, hole: int) -> str:
        """구멍을 친다. 결과('hit'|'trap'|'empty')를 반환한다."""
        if self.over or hole not in self.moles:
            self.combo = 0                       # 헛스윙 → 콤보 끊김
            self.events.append(("empty", hole))
            return "empty"
        kind = self.moles.pop(hole)["kind"]
        if kind == "trap":                       # 함정을 침 → 감점
            self.misses += 1
            self.combo = 0
            self.coins = max(0, self.coins - config.WHACK_TRAP_PENALTY)
            self.events.append(("trap", hole))
            return "trap"
        # 두더지 명중 → 점수 + 콤보 보너스
        self.hits += 1
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        bonus = (self.combo // config.WHACK_COMBO_STEP) * config.WHACK_COMBO_BONUS
        self.coins += config.WHACK_HIT_REWARD + bonus
        self.events.append(("hit", hole))
        return "hit"


class WhackAMole(MiniGame):
    name = "두더지 잡기"

    # 구멍 중심 좌표(128×64 캔버스). 인덱스 0·1·2 = 왼·가운데·오른쪽.
    _HOLE_CX = (24, 64, 104)
    _HOLE_CY = 32
    _HOLE_R = 12
    _HINT = ("◀", "▼", "▶")     # 폰트에 있는 삼각형으로 버튼 위치 표시(화살표 대체)

    def __init__(self, ctx=None, rng=None) -> None:
        self.ctx = ctx
        self.engine = WhackEngine(rng=rng)
        self._frame = 0

    def play(self) -> int:
        ctx = self.ctx
        if ctx is None:
            return 0
        # 두더지 잡기 동안에는 3버튼이 확인/뒤로가 아니라 구멍(0·1·2) 전용이 된다.
        ctx.set_button_actions(config.BUTTON_GAME_ACTIONS)
        aborted = False
        try:
            while ctx.running and not self.engine.over:
                for a in ctx.poll():
                    if a == "b":            # (PC ESC 등) 중단
                        aborted = True
                        break
                    if a in ACTION_HOLE:
                        self.engine.whack(ACTION_HOLE[a])
                if aborted:
                    break
                dt = ctx.tick()
                self.engine.update(dt)
                self._feedback()
                self._render()
                self._frame += 1
        finally:
            ctx.leds_off()
            ctx.use_menu_buttons()          # 게임오버·메뉴를 위해 버튼을 확인/뒤로로 복귀
        return self._finish()

    # ── 출력: 부저 + LED ─────────────────────────────────
    def _feedback(self) -> None:
        ctx = self.ctx
        for kind, _hole in self.engine.events:
            if kind == "hit":
                ctx.beep(988, 0.02)
            elif kind == "spawn":
                ctx.beep(1245, 0.01)
            elif kind == "trap":
                ctx.beep(294, 0.05)
            elif kind == "miss":
                ctx.beep(392, 0.03)
        self.engine.events.clear()
        # LED: 두더지=점등, 함정=깜빡임(구분), 빈 구멍=소등
        blink_on = (self._frame // 3) % 2 == 0
        for i in range(HOLES):
            m = self.engine.moles.get(i)
            on = bool(m) and (m["kind"] == "mole" or blink_on)
            ctx.led(i, on)

    # ── 출력: 화면 ───────────────────────────────────────
    def _render(self) -> None:
        ctx = self.ctx
        e = self.engine
        ctx.clear()
        # 남은 시간 막대(상단)
        ratio = max(0.0, 1.0 - e._progress())
        ctx.rect(0, 0, int(ctx.width * ratio), 3, config.COLOR_ACCENT)
        # 점수 · 콤보
        ctx.text(f"{e.coins}", 2, 6, color=config.COLOR_WARN, small=True)
        if e.combo >= 2:
            ctx.text(f"x{e.combo}", ctx.width - 22, 6,
                     color=config.COLOR_ACCENT, small=True)
        # 구멍 3개
        blink_on = (self._frame // 3) % 2 == 0
        for i in range(HOLES):
            cx, cy, r = self._HOLE_CX[i], self._HOLE_CY, self._HOLE_R
            ctx.circle(cx, cy, r, config.COLOR_DIM, fill=False)   # 구멍 테두리
            m = e.moles.get(i)
            if m and m["kind"] == "mole":
                ctx.circle(cx, cy, r - 3, config.COLOR_ACCENT)
                ctx.circle(cx - 4, cy - 2, 2, (30, 30, 40))       # 눈
                ctx.circle(cx + 4, cy - 2, 2, (30, 30, 40))
            elif m and m["kind"] == "trap" and blink_on:          # 함정: 깜빡이는 ✕
                ctx.circle(cx, cy, r - 3, config.COLOR_WARN, fill=False)
                ctx.line(cx - 4, cy - 4, cx + 4, cy + 4, config.COLOR_WARN)
                ctx.line(cx - 4, cy + 4, cx + 4, cy - 4, config.COLOR_WARN)
            # 버튼 위치 힌트
            ctx.text(self._HINT[i], cx - 4, cy + r + 2,
                     color=config.COLOR_DIM, small=True)
        ctx.present()

    # ── 종료 ─────────────────────────────────────────────
    def _finish(self) -> int:
        if self.ctx.running:
            self._game_over()
        return self.engine.coins

    def _game_over(self) -> None:
        ctx = self.ctx
        e = self.engine
        ctx.clear()
        ctx.text("끝!", ctx.width // 2, 14, big=True, center=True)
        ctx.text(f"점수 {e.coins}  최고콤보 {e.max_combo}", ctx.width // 2, 34,
                 center=True, small=True)
        ctx.text(f"명중 {e.hits}  놓침 {e.misses}", ctx.width // 2, 48,
                 center=True, small=True)
        ctx.present()
        ctx.wait_action({"a", "b"})
