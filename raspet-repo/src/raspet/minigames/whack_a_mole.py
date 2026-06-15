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

    def __init__(self, rng=None, duration=None, holes=HOLES) -> None:
        self.rng = rng or random.Random()
        self.duration = config.WHACK_DURATION_S if duration is None else duration
        self.holes = holes          # 구멍(셀) 개수. 기본 3(버튼 모드), 키패드는 4×4=16.
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
        free = [i for i in range(self.holes) if i not in self.moles]
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
        self._rng = rng
        self.engine = None          # play()에서 모드(구멍 수)를 정한 뒤 생성
        self._frame = 0
        self._best = 0              # 시작 전 베스트 기록(플레이 중·종료 화면 표시용)
        self._grid = (1, HOLES)     # (행, 열) — 키패드면 4×4, 아니면 1×3
        self._keypad = None         # 그리드 모드에서 직접 읽을 키패드

    def play(self) -> int:
        ctx = self.ctx
        if ctx is None:
            return 0
        # 시작 전 베스트 기록을 읽어둔다(헤드리스/테스트는 app이 없을 수 있어 안전 접근).
        ch = getattr(getattr(ctx, "app", None), "character", None)
        if ch is not None:
            self._best = ch.best_score(self.name)
        # 입력 모드 결정: 4×4 키패드가 있으면 OLED 격자 모드, 없으면 기존 3구멍(버튼) 모드.
        keypad = ctx.hw.get("keypad")
        grid_mode = keypad is not None and getattr(keypad, "available", False)
        if grid_mode:
            rows, cols = config.WHACK_GRID_ROWS, config.WHACK_GRID_COLS
            self._keypad = keypad
            ctx.set_keypad_mode("grid")     # poll()이 키패드를 소비하지 않게 → 직접 읽는다
        else:
            rows, cols = 1, HOLES
            ctx.set_button_actions(config.BUTTON_GAME_ACTIONS)  # 3버튼=구멍(0·1·2)
        self._grid = (rows, cols)
        self.engine = WhackEngine(rng=self._rng, holes=rows * cols)
        try:
            self._loop(grid_mode)
        finally:
            ctx.leds_off()
            if grid_mode:
                ctx.set_keypad_mode("menu")
            else:
                ctx.use_menu_buttons()      # 게임오버·메뉴용으로 버튼을 확인/뒤로로 복귀
        return self._finish()

    def _loop(self, grid_mode) -> None:
        ctx = self.ctx
        while ctx.running and not self.engine.over:
            actions = ctx.poll()
            if "b" in actions:              # 키보드 ESC / 조이스틱 등으로 중단
                break
            if grid_mode:
                if self._read_keypad():     # 뒤로 키 → 중단
                    break
            else:
                for a in actions:
                    if a in ACTION_HOLE:
                        self.engine.whack(ACTION_HOLE[a])
            self.engine.update(ctx.tick())
            self._feedback(grid_mode)
            if grid_mode:
                self._render_grid()
            else:
                self._render_holes()
            self._frame += 1

    def _read_keypad(self) -> bool:
        """그리드 모드: 키패드로 눌린 셀을 친다. 뒤로 키가 눌리면 True(중단)."""
        _, cols = self._grid
        for (r, c) in self._keypad.pressed_edges():
            if self._keypad.key_label(r, c) == config.KEYPAD_BACK_KEY:
                return True
            idx = r * cols + c
            if 0 <= idx < self.engine.holes:
                self.engine.whack(idx)
        return False

    # ── 출력: 부저 + LED ─────────────────────────────────
    def _feedback(self, grid_mode) -> None:
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
        blink_on = (self._frame // 3) % 2 == 0
        if grid_mode:
            # 셀이 16개라 칸마다 LED를 줄 수 없으므로 3 LED를 전역 표시등으로 쓴다:
            #   초록(0)=콤보 중, 빨강(1)=함정이 떠 있음(주의), 노랑(2)=두더지 등장 중.
            any_trap = any(m["kind"] == "trap" for m in self.engine.moles.values())
            any_mole = any(m["kind"] == "mole" for m in self.engine.moles.values())
            ctx.led(0, self.engine.combo >= config.WHACK_COMBO_STEP)
            ctx.led(1, any_trap and blink_on)
            ctx.led(2, any_mole)
        else:
            # LED: 두더지=점등, 함정=깜빡임(구분), 빈 구멍=소등
            for i in range(HOLES):
                m = self.engine.moles.get(i)
                on = bool(m) and (m["kind"] == "mole" or blink_on)
                ctx.led(i, on)

    # ── 출력: 공통 HUD ───────────────────────────────────
    def _hud(self) -> None:
        ctx, e = self.ctx, self.engine
        ctx.rect(0, 0, int(ctx.width * max(0.0, 1.0 - e._progress())), 3,
                 config.COLOR_ACCENT)                    # 남은 시간 막대
        ctx.text(f"{e.coins}", 2, 6, color=config.COLOR_WARN, small=True)
        ctx.text(f"최고 {self._best}", ctx.width // 2, 8,
                 color=config.COLOR_DIM, small=True, center=True)
        if e.combo >= 2:
            ctx.text(f"x{e.combo}", ctx.width - 22, 6,
                     color=config.COLOR_ACCENT, small=True)

    # ── 출력: 기존 3구멍(버튼) 화면 ──────────────────────
    def _render_holes(self) -> None:
        ctx, e = self.ctx, self.engine
        ctx.clear()
        self._hud()
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
            ctx.text(self._HINT[i], cx - 4, cy + r + 2,
                     color=config.COLOR_DIM, small=True)
        ctx.present()

    # ── 출력: 4×4 키패드 격자 화면 ───────────────────────
    def _render_grid(self) -> None:
        ctx, e = self.ctx, self.engine
        rows, cols = self._grid
        ctx.clear()
        self._hud()
        top = 13                                  # HUD 아래부터 격자 시작
        cell_w = ctx.width // cols
        cell_h = (ctx.height - top) // rows
        blink_on = (self._frame // 3) % 2 == 0
        for idx in range(self.engine.holes):
            r, c = idx // cols, idx % cols
            x, y = c * cell_w, top + r * cell_h
            cx, cy = x + cell_w // 2, y + cell_h // 2
            rad = max(2, min(cell_w, cell_h) // 2 - 2)
            ctx.rect(x + 1, y + 1, cell_w - 2, cell_h - 2,
                     config.COLOR_DIM, fill=False)              # 셀 테두리
            m = e.moles.get(idx)
            if m and m["kind"] == "mole":
                ctx.circle(cx, cy, rad, config.COLOR_ACCENT)
                ctx.circle(cx - rad // 2, cy - 1, 1, (30, 30, 40))   # 눈
                ctx.circle(cx + rad // 2, cy - 1, 1, (30, 30, 40))
            elif m and m["kind"] == "trap" and blink_on:
                ctx.line(cx - rad, cy - rad, cx + rad, cy + rad, config.COLOR_WARN)
                ctx.line(cx - rad, cy + rad, cx + rad, cy - rad, config.COLOR_WARN)
            else:
                # 빈 칸: 어떤 키를 누르면 되는지 키패드 라벨을 흐리게 표시
                label = self._keypad.key_label(r, c) if self._keypad else ""
                if label:
                    ctx.text(label, x + 2, y + 1, color=config.COLOR_DIM, small=True)
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
        new_record = e.coins > self._best
        title = "신기록!" if new_record else "끝!"
        color = config.COLOR_ACCENT if new_record else config.COLOR_FG
        ctx.text(title, ctx.width // 2, 12, big=True, center=True, color=color)
        best_now = max(self._best, e.coins)
        ctx.text(f"점수 {e.coins}  최고 {best_now}", ctx.width // 2, 30,
                 center=True, small=True)
        ctx.text(f"콤보 {e.max_combo}  명중 {e.hits}  놓침 {e.misses}", ctx.width // 2, 44,
                 center=True, small=True)
        ctx.present()
        ctx.wait_action({"a", "b"})
