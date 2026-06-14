"""구체 씬들 — 메뉴 · 육성(돌보기) · 미니게임 · 상점 · 엔딩.

각 씬은 Scene 인터페이스를 따르며, app(GameLoop)을 통해 ctx와 캐릭터에 접근한다.
미니게임 실행 글루(launcher)도 여기 둔다 — 미니게임 모듈끼리는 서로 의존하지 않게
하고, 앱 계층에서만 조립한다.
"""
from .scene import Scene
from .. import config
from ..character import needs
from ..character.endings import determine_ending
from ..minigames.omok import Omok, HUMAN, AI, EMPTY
from ..minigames.rps import RockPaperScissors
from ..minigames.snake import Snake
from ..minigames.jump import UltrasonicJump
from ..minigames.color_hunt import ColorHunt


class AbortGame(Exception):
    """미니게임 도중 창이 닫히는 등으로 중단할 때 사용."""


# ── 공통 메뉴 위젯 ───────────────────────────────────────
class Menu:
    """위/아래로 이동하는 세로 메뉴."""

    def __init__(self, items: list[str]) -> None:
        self.items = items
        self.index = 0

    def move(self, action: str) -> None:
        if action == "up":
            self.index = (self.index - 1) % len(self.items)
        elif action == "down":
            self.index = (self.index + 1) % len(self.items)

    @property
    def selected(self) -> str:
        return self.items[self.index]

    def render(self, ctx, x=6, y=18, line=11) -> None:
        for i, item in enumerate(self.items):
            sel = (i == self.index)
            color = config.COLOR_ACCENT if sel else config.COLOR_FG
            prefix = "▶ " if sel else "  "
            ctx.text(prefix + item, x, y + i * line, color=color)


# ── 메뉴 씬 ──────────────────────────────────────────────
class MenuScene(Scene):
    _ITEMS = ["돌보기", "미니게임", "상점", "엔딩 보기"]

    def __init__(self) -> None:
        self.menu = Menu(self._ITEMS)

    def handle_input(self, actions, app) -> None:
        for a in actions:
            self.menu.move(a)
            if a == "a":
                self._select(app)

    def _select(self, app) -> None:
        choice = self.menu.selected
        if choice == "돌보기":
            app.switch(CareScene())
        elif choice == "미니게임":
            app.switch(MiniGameMenuScene())
        elif choice == "상점":
            app.switch(ShopScene())
        elif choice == "엔딩 보기":
            app.switch(EndingScene())

    def render(self, ctx) -> None:
        c = ctx.app.character if hasattr(ctx, "app") else None
        ctx.clear()
        ctx.text("RasPet", 6, 4, color=config.COLOR_ACCENT)
        self.menu.render(ctx)


# ── 돌보기(육성) 씬 ──────────────────────────────────────
class CareScene(Scene):
    # (라벨, 동작) — 동작은 app, character를 받는다
    _ACTIONS = [
        ("먹이주기", lambda ch: needs.feed(ch)),
        ("씻기기", lambda ch: needs.clean(ch)),
        ("놀아주기", lambda ch: needs.play_with(ch)),
        ("근력훈련", lambda ch: ch.train("strength")),
        ("지력훈련", lambda ch: ch.train("intellect")),
        ("매력훈련", lambda ch: ch.train("charm")),
        ("감수성훈련", lambda ch: ch.train("sensitivity")),
        ("뒤로", None),
    ]

    def __init__(self) -> None:
        self.menu = Menu([label for label, _ in self._ACTIONS])

    def handle_input(self, actions, app) -> None:
        for a in actions:
            self.menu.move(a)
            if a == "b":
                app.switch(MenuScene())
            elif a == "a":
                self._do(app)

    def _do(self, app) -> None:
        label, fn = self._ACTIONS[self.menu.index]
        if fn is None:
            app.switch(MenuScene())
        else:
            fn(app.character)
            app.ctx.beep(660, 0.03)

    def render(self, ctx) -> None:
        ch = ctx.app.character
        ctx.clear()
        ctx.text(f"{ch.name} Lv.{ch.stage}  C:{ch.currency}", 4, 2,
                 color=config.COLOR_ACCENT)
        self.menu.render(ctx, x=4, y=14, line=10)
        # 우측에 주요 상태 요약
        rx = 74
        lines = [f"포만 {ch.fullness}", f"청결 {ch.cleanliness}",
                 f"행복 {ch.happiness}", f"스트 {ch.stress}",
                 f"근 {ch.strength} 지 {ch.intellect}",
                 f"매 {ch.charm} 감 {ch.sensitivity}"]
        for i, s in enumerate(lines):
            ctx.text(s, rx, 14 + i * 9, color=config.COLOR_DIM)


# ── 미니게임 선택 씬 ─────────────────────────────────────
class MiniGameMenuScene(Scene):
    _GAMES = ["오목", "가위바위보", "스네이크", "초음파 점프", "색깔 찾기", "뒤로"]

    def __init__(self) -> None:
        self.menu = Menu(self._GAMES)
        self.last_reward = None

    def handle_input(self, actions, app) -> None:
        for a in actions:
            self.menu.move(a)
            if a == "b":
                app.switch(MenuScene())
            elif a == "a":
                self._launch(app)

    def _launch(self, app) -> None:
        choice = self.menu.selected
        if choice == "뒤로":
            app.switch(MenuScene())
            return
        reward = run_minigame(choice, app.ctx)
        app.character.currency += reward
        self.last_reward = (choice, reward)
        app.ctx.beep(880, 0.05)

    def render(self, ctx) -> None:
        ctx.clear()
        ctx.text("미니게임", 6, 2, color=config.COLOR_ACCENT)
        self.menu.render(ctx, y=14, line=9)
        if self.last_reward:
            name, reward = self.last_reward
            ctx.text(f"+{reward} ({name})", 6, ctx.height - 9,
                     color=config.COLOR_WARN)


# ── 상점 씬 ──────────────────────────────────────────────
class ShopScene(Scene):
    def __init__(self) -> None:
        self.shop = None
        self.menu = None
        self.msg = ""

    def _ensure(self, app) -> None:
        if self.shop is None:
            self.shop = app.shop
            labels = [f"{it.name} {it.price}" for it in self.shop.catalog]
            labels.append("뒤로")
            self.menu = Menu(labels)

    def handle_input(self, actions, app) -> None:
        self._ensure(app)
        for a in actions:
            self.menu.move(a)
            if a == "b":
                app.switch(MenuScene())
            elif a == "a":
                self._buy(app)

    def _buy(self, app) -> None:
        if self.menu.index >= len(self.shop.catalog):   # "뒤로"
            app.switch(MenuScene())
            return
        item = self.shop.catalog[self.menu.index]
        if self.shop.buy(app.character, item):
            self.msg = f"{item.name} 구매!"
            app.ctx.beep(990, 0.04)
        else:
            self.msg = "재화 부족"

    def render(self, ctx) -> None:
        self._ensure(ctx.app)
        ch = ctx.app.character
        ctx.clear()
        ctx.text(f"상점  C:{ch.currency}", 4, 2, color=config.COLOR_ACCENT)
        self.menu.render(ctx, x=4, y=13, line=8)
        if self.msg:
            ctx.text(self.msg, 4, ctx.height - 9, color=config.COLOR_WARN)


# ── 엔딩 씬 ──────────────────────────────────────────────
class EndingScene(Scene):
    def handle_input(self, actions, app) -> None:
        if actions:
            app.switch(MenuScene())

    def render(self, ctx) -> None:
        ending = determine_ending(ctx.app.character)
        ctx.clear()
        ctx.text("엔딩", ctx.width // 2, 6, color=config.COLOR_DIM, center=True)
        ctx.text(ending["title"], ctx.width // 2, 22,
                 color=config.COLOR_ACCENT, big=True, center=True)
        # 설명을 화면 폭에 맞춰 단순 줄바꿈
        desc = ending["desc"]
        for i, line in enumerate(_wrap(desc, 18)):
            ctx.text(line, ctx.width // 2, 40 + i * 9, center=True)


def _wrap(text: str, width: int) -> list[str]:
    out, cur = [], ""
    for ch in text:
        cur += ch
        if len(cur) >= width:
            out.append(cur)
            cur = ""
    if cur:
        out.append(cur)
    return out


# ── 미니게임 실행 글루 ───────────────────────────────────
def run_minigame(name: str, ctx) -> int:
    """이름으로 미니게임을 만들어 실행하고 보상을 반환한다."""
    try:
        if name == "오목":
            controller = OmokController(ctx)
            game = Omok(difficulty="normal",
                        move_provider=controller.move_provider,
                        renderer=controller.render)
            return game.play()
        if name == "가위바위보":
            return RockPaperScissors(ctx=ctx).play()
        if name == "스네이크":
            return Snake(ctx=ctx).play()
        if name == "초음파 점프":
            return UltrasonicJump(ctx=ctx).play()
        if name == "색깔 찾기":
            return ColorHunt(ctx=ctx).play()
    except AbortGame:
        return 0
    return 0


class OmokController:
    """ctx 입력/렌더를 오목의 move_provider/renderer로 이어주는 어댑터."""

    def __init__(self, ctx) -> None:
        self.ctx = ctx
        size = config.OMOK_BOARD_SIZE
        self.cursor = [size // 2, size // 2]
        self.size = size

    def move_provider(self, board):
        """커서를 움직여 빈 칸에서 'a'를 누르면 그 좌표를 반환한다."""
        ctx = self.ctx
        while True:
            if not ctx.running:
                raise AbortGame
            for a in ctx.poll():
                if a == "b":
                    raise AbortGame
                self._move_cursor(a)
                if a == "a":
                    r, c = self.cursor
                    if board[r][c] == EMPTY:
                        return (r, c)
            self.render(board, {})
            ctx.tick()

    def _move_cursor(self, a) -> None:
        r, c = self.cursor
        if a == "up":
            r = max(0, r - 1)
        elif a == "down":
            r = min(self.size - 1, r + 1)
        elif a == "left":
            c = max(0, c - 1)
        elif a == "right":
            c = min(self.size - 1, c + 1)
        self.cursor = [r, c]

    def render(self, board, info) -> None:
        ctx = self.ctx
        cell = min(ctx.width, ctx.height) // self.size
        ox = (ctx.width - cell * self.size) // 2
        oy = (ctx.height - cell * self.size) // 2
        ctx.clear()
        for r in range(self.size):
            for c in range(self.size):
                x, y = ox + c * cell, oy + r * cell
                v = board[r][c]
                if v == HUMAN:
                    ctx.rect(x, y, cell, cell, config.COLOR_FG)
                elif v == AI:
                    ctx.rect(x, y, cell, cell, config.COLOR_WARN)
                else:
                    ctx.rect(x, y, cell, cell, config.COLOR_DIM, fill=False)
        cr, cc = self.cursor
        ctx.rect(ox + cc * cell, oy + cr * cell, cell, cell,
                 config.COLOR_ACCENT, fill=False)
        ctx.present()
