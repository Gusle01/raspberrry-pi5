"""구체 씬들 — 타이틀 · 메뉴(홈) · 육성 · 미니게임 · 상점 · 업적 · 엔딩 · 팝업.

각 씬은 Scene 인터페이스를 따르며, app(GameLoop)을 통해 ctx와 캐릭터에 접근한다.
미니게임 실행 글루(launcher)도 여기 둔다 — 미니게임 모듈끼리는 서로 의존하지 않게
하고, 앱 계층에서만 조립한다.
"""
from .scene import Scene
from .sprite import draw_pet
from . import daytime, sfx
from .. import config, events, achievements
from ..character import needs
from ..character.mood import mood_label
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
            prefix = "▶" if sel else " "
            ctx.text(prefix + item, x, y + i * line, color=color)


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


def _bg(ctx) -> None:
    """현재 시간대 색조로 배경을 칠한다."""
    ctx.clear(daytime.tint(daytime.current_period()))


# ── 팝업 씬 (이벤트·업적 알림 공용) ──────────────────────
class PopupScene(Scene):
    """제목/설명 팝업을 차례로 보여주고 끝나면 return_scene으로 돌아간다."""

    def __init__(self, popups: list[dict], return_scene: Scene) -> None:
        self.popups = popups
        self.return_scene = return_scene
        self.i = 0

    def handle_input(self, actions, app) -> None:
        if actions:
            self.i += 1
            if self.i >= len(self.popups):
                app.switch(self.return_scene)

    def render(self, ctx) -> None:
        p = self.popups[min(self.i, len(self.popups) - 1)]
        ctx.clear()
        ctx.rect(6, 8, ctx.width - 12, ctx.height - 16, p["color"], fill=False)
        ctx.text(p["title"], ctx.width // 2, 18, color=p["color"],
                 big=True, center=True)
        for j, line in enumerate(_wrap(p["desc"], 18)):
            ctx.text(line, ctx.width // 2, 34 + j * 9, center=True)
        ctx.text("(아무 키)", ctx.width // 2, ctx.height - 8,
                 color=config.COLOR_DIM, center=True)


def _event_popup(ev: dict) -> dict:
    return {"title": ev["title"], "desc": ev["desc"], "color": config.COLOR_WARN}


def _ach_popup(ach: dict) -> dict:
    return {"title": "업적 달성! " + ach["title"], "desc": ach["desc"],
            "color": config.COLOR_ACCENT}


def _progress_popups(app, before_event: dict | None = None) -> list[dict]:
    """이벤트(선택) + 새로 해금된 업적을 팝업 목록으로 만든다."""
    popups = []
    if before_event:
        sfx.event(app.ctx)
        popups.append(_event_popup(before_event))
    newly = achievements.check_and_unlock(app.character)
    if newly:
        sfx.achievement(app.ctx)
        popups.extend(_ach_popup(a) for a in newly)
    return popups


def _go(app, return_scene, popups) -> None:
    """팝업이 있으면 팝업을 거쳐, 없으면 곧장 return_scene으로 전환."""
    if popups:
        app.switch(PopupScene(popups, return_scene))
    else:
        app.switch(return_scene)


# ── 타이틀 씬 ────────────────────────────────────────────
class TitleScene(Scene):
    def __init__(self) -> None:
        self._t = 0.0

    def handle_input(self, actions, app) -> None:
        if actions:
            sfx.confirm(app.ctx)
            app.switch(MenuScene())

    def update(self, dt, app) -> None:
        self._t += dt

    def render(self, ctx) -> None:
        _bg(ctx)
        ch = ctx.app.character
        draw_pet(ctx, ch, ctx.width // 2, 24, scale=1.4)
        ctx.text("RasPet", ctx.width // 2, 44, color=config.COLOR_ACCENT,
                 big=True, center=True)
        if int(self._t * 2) % 2 == 0:        # 깜빡이는 안내
            ctx.text("아무 키나 누르세요", ctx.width // 2, ctx.height - 8,
                     color=config.COLOR_DIM, center=True)


# ── 메뉴(홈) 씬 ──────────────────────────────────────────
class MenuScene(Scene):
    _ITEMS = ["돌보기", "미니게임", "상점", "탐험", "업적", "엔딩"]

    def __init__(self) -> None:
        self.menu = Menu(self._ITEMS)

    def handle_input(self, actions, app) -> None:
        for a in actions:
            if a in ("up", "down"):
                self.menu.move(a)
            elif a == "a":
                self._select(app)

    def _select(self, app) -> None:
        choice = self.menu.selected
        sfx.confirm(app.ctx)
        if choice == "돌보기":
            app.switch(CareScene())
        elif choice == "미니게임":
            app.switch(MiniGameMenuScene())
        elif choice == "상점":
            app.switch(ShopScene())
        elif choice == "탐험":
            self._explore(app)
        elif choice == "업적":
            app.switch(AchievementScene())
        elif choice == "엔딩":
            app.switch(EndingScene())

    def _explore(self, app) -> None:
        ev = events.force_event(app.character, app.rng)
        _go(app, self, _progress_popups(app, before_event=ev))

    def render(self, ctx) -> None:
        ch = ctx.app.character
        period = daytime.current_period()
        ctx.clear(daytime.tint(period))
        draw_pet(ctx, ch, 26, 30, scale=1.2)
        ctx.text(f"{ch.name} Lv.{ch.stage}", 4, 2, color=config.COLOR_ACCENT)
        ctx.text(f"C:{ch.currency}", 4, ctx.height - 9, color=config.COLOR_WARN)
        self.menu.render(ctx, x=66, y=8, line=9)


# ── 돌보기(육성) 씬 ──────────────────────────────────────
class CareScene(Scene):
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
            if a in ("up", "down"):
                self.menu.move(a)
            elif a == "b":
                app.switch(MenuScene())
            elif a == "a":
                self._do(app)

    def _do(self, app) -> None:
        label, fn = self._ACTIONS[self.menu.index]
        if fn is None:
            sfx.cancel(app.ctx)
            app.switch(MenuScene())
            return
        fn(app.character)
        sfx.confirm(app.ctx)
        # 훈련으로 능력치 임계값을 넘으면 업적이 해금될 수 있다.
        popups = _progress_popups(app)
        if popups:
            app.switch(PopupScene(popups, self))

    def render(self, ctx) -> None:
        ch = ctx.app.character
        _bg(ctx)
        draw_pet(ctx, ch, 100, 18, scale=0.8)
        ctx.text(mood_label(ch), 78, 32, color=config.COLOR_DIM)
        self.menu.render(ctx, x=2, y=2, line=7)
        ctx.text(f"포{ch.fullness} 청{ch.cleanliness}", 70, 44,
                 color=config.COLOR_DIM)
        ctx.text(f"행{ch.happiness} 스{ch.stress}", 70, 54,
                 color=config.COLOR_DIM)


# ── 미니게임 선택 씬 ─────────────────────────────────────
class MiniGameMenuScene(Scene):
    _GAMES = ["오목", "가위바위보", "스네이크", "초음파 점프", "색깔 찾기", "뒤로"]

    def __init__(self) -> None:
        self.menu = Menu(self._GAMES)
        self.last_reward = None

    def handle_input(self, actions, app) -> None:
        for a in actions:
            if a in ("up", "down"):
                self.menu.move(a)
            elif a == "b":
                app.switch(MenuScene())
            elif a == "a":
                self._launch(app)

    def _launch(self, app) -> None:
        choice = self.menu.selected
        if choice == "뒤로":
            sfx.cancel(app.ctx)
            app.switch(MenuScene())
        elif choice == "오목":
            app.switch(DifficultyScene(self))     # 난이도 먼저 선택
        else:
            play_and_reward(app, self, choice)

    def render(self, ctx) -> None:
        _bg(ctx)
        ctx.text("미니게임", 6, 2, color=config.COLOR_ACCENT)
        self.menu.render(ctx, y=13, line=8)
        if self.last_reward:
            name, reward = self.last_reward
            ctx.text(f"+{reward} ({name})", 6, ctx.height - 9,
                     color=config.COLOR_WARN)


# ── 오목 난이도 선택 씬 ──────────────────────────────────
class DifficultyScene(Scene):
    _LEVELS = [("쉬움", "easy"), ("보통", "normal"), ("어려움", "hard"), ("뒤로", None)]

    def __init__(self, menu_scene: Scene) -> None:
        self.menu_scene = menu_scene
        self.menu = Menu([label for label, _ in self._LEVELS])

    def handle_input(self, actions, app) -> None:
        for a in actions:
            if a in ("up", "down"):
                self.menu.move(a)
            elif a == "b":
                app.switch(self.menu_scene)
            elif a == "a":
                _, diff = self._LEVELS[self.menu.index]
                if diff is None:
                    app.switch(self.menu_scene)
                else:
                    play_and_reward(app, self.menu_scene, "오목", diff)

    def render(self, ctx) -> None:
        _bg(ctx)
        ctx.text("오목 난이도", 6, 4, color=config.COLOR_ACCENT)
        self.menu.render(ctx, y=20, line=10)


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
            if a in ("up", "down"):
                self.menu.move(a)
            elif a == "b":
                app.switch(MenuScene())
            elif a == "a":
                self._buy(app)

    def _buy(self, app) -> None:
        if self.menu.index >= len(self.shop.catalog):   # "뒤로"
            sfx.cancel(app.ctx)
            app.switch(MenuScene())
            return
        item = self.shop.catalog[self.menu.index]
        if self.shop.buy(app.character, item):
            self.msg = f"{item.name} 구매!"
            sfx.confirm(app.ctx)
            popups = _progress_popups(app)     # 아이템 효과로 업적 해금 가능
            if popups:
                app.switch(PopupScene(popups, self))
        else:
            self.msg = "재화 부족"
            sfx.cancel(app.ctx)

    def render(self, ctx) -> None:
        self._ensure(ctx.app)
        ch = ctx.app.character
        _bg(ctx)
        ctx.text(f"상점  C:{ch.currency}", 4, 2, color=config.COLOR_ACCENT)
        self.menu.render(ctx, x=4, y=13, line=8)
        if self.msg:
            ctx.text(self.msg, 4, ctx.height - 9, color=config.COLOR_WARN)


# ── 업적 씬 ──────────────────────────────────────────────
class AchievementScene(Scene):
    def __init__(self) -> None:
        self.scroll = 0

    def handle_input(self, actions, app) -> None:
        total = len(config.ACHIEVEMENTS)
        for a in actions:
            if a == "down":
                self.scroll = min(self.scroll + 1, max(0, total - 5))
            elif a == "up":
                self.scroll = max(self.scroll - 1, 0)
            elif a == "b":
                app.switch(MenuScene())

    def render(self, ctx) -> None:
        ch = ctx.app.character
        _bg(ctx)
        ctx.text("업적", 6, 2, color=config.COLOR_ACCENT)
        rows = achievements.all_with_status(ch)
        for i, (ach, owned) in enumerate(rows[self.scroll:self.scroll + 5]):
            mark = "✔" if owned else "·"
            color = config.COLOR_ACCENT if owned else config.COLOR_DIM
            ctx.text(f"{mark} {ach['title']}", 4, 14 + i * 10, color=color)


# ── 엔딩 씬 ──────────────────────────────────────────────
class EndingScene(Scene):
    def handle_input(self, actions, app) -> None:
        if actions:
            app.switch(MenuScene())

    def render(self, ctx) -> None:
        ch = ctx.app.character
        ending = determine_ending(ch)
        _bg(ctx)
        draw_pet(ctx, ch, ctx.width // 2, 14, scale=0.8)
        ctx.text(ending["title"], ctx.width // 2, 30,
                 color=config.COLOR_ACCENT, big=True, center=True)
        for i, line in enumerate(_wrap(ending["desc"], 18)):
            ctx.text(line, ctx.width // 2, 44 + i * 9, center=True)


# ── 미니게임 실행 + 보상/이벤트/업적 처리 ────────────────
def play_and_reward(app, return_scene, name, difficulty="normal") -> int:
    """미니게임을 실행하고 보상·통계·이벤트·업적까지 처리한 뒤 전환한다."""
    ctx = app.ctx
    reward = run_minigame(name, ctx, difficulty)
    ch = app.character
    ch.currency += reward
    ch.total_earned += reward
    ch.games_played += 1
    if reward > 0:
        sfx.win(ctx)
    if hasattr(return_scene, "last_reward"):
        return_scene.last_reward = (name, reward)
    ev = events.maybe_trigger(ch, app.rng)
    _go(app, return_scene, _progress_popups(app, before_event=ev))
    return reward


def run_minigame(name: str, ctx, difficulty: str = "normal") -> int:
    """이름으로 미니게임을 만들어 실행하고 보상을 반환한다."""
    try:
        if name == "오목":
            controller = OmokController(ctx)
            game = Omok(difficulty=difficulty,
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
