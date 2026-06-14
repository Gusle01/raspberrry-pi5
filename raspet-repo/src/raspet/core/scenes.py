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
from ..minigames.whack_a_mole import WhackAMole


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

    def render(self, ctx, x=6, y=2, line=None, small=True) -> None:
        """항목을 세로로 그린다(y부터 캔버스 바닥까지 사용).

        가능하면 줄 간격을 좁혀서라도 **전부** 보이게 하고, 그래도 영역을 넘으면
        선택 항목을 따라 스크롤하며 가려진 쪽에 ▲/▼를 표시한다. 어떤 경우에도
        항목이 캔버스(GAME_H) 밖으로 잘리지 않는다.
        """
        font = ctx.font_small if small else ctx.font
        fh = font.get_height()
        n = len(self.items)
        avail = ctx.height - y                      # 메뉴가 쓸 수 있는 세로 공간

        if line is None:
            # 마지막 항목 바닥 = (k-1)*line + fh 이므로, n개가 들어갈 최대 줄간격은
            # (avail - fh) // (n-1). 이 공식으로 off-by-one 없이 정확히 맞춘다.
            fit = (avail - fh) // (n - 1) if n > 1 else avail
            min_line = max(8, fh - 3)               # 가독 한계까지 좁혀 더 담는다
            if fit >= fh + 1:
                line = fh + 1                       # 여유 충분 → 보기 좋은 간격
            elif fit >= min_line:
                line = fit                          # 살짝 좁혀 전부 표시
            else:
                line = fh + 1                       # 한 화면에 불가 → 스크롤

        # 마지막 항목 바닥이 avail 안에 들어오는 최대 개수 = (avail - fh)//line + 1
        visible = max(1, (avail - fh) // line + 1)
        if visible >= n:                            # 전부 보임
            visible, start = n, 0
        else:                                       # 스크롤: 선택 항목을 가운데 부근에
            start = min(max(0, self.index - visible // 2), n - visible)

        for row, i in enumerate(range(start, start + visible)):
            sel = (i == self.index)
            color = config.COLOR_ACCENT if sel else config.COLOR_FG
            prefix = "▶" if sel else " "
            ctx.text(prefix + self.items[i], x, y + row * line, color=color, small=small)

        # 스크롤 표시(가려진 항목이 있을 때만)
        ind_x = ctx.width - 8
        if start > 0:
            ctx.text("▲", ind_x, y, color=config.COLOR_FG, small=small)
        if start + visible < n:
            ctx.text("▼", ind_x, y + (visible - 1) * line, color=config.COLOR_FG, small=small)


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
        cx = ctx.width // 2
        # center=True 일 때 y는 글자의 '세로 중심'이다. 박스 폭에 맞게 제목을
        # 줄바꿈(최대 2줄)해 가로 넘침을 막고, 본문은 작은 폰트로 하단에 둔다.
        for k, line in enumerate(_wrap(p["title"], 8)[:2]):
            ctx.text(line, cx, 12 + k * 15, color=p["color"], center=True)  # 중심 12,27 → 바닥 ≤35
        for j, line in enumerate(_wrap(p["desc"], 18)[:2]):
            ctx.text(line, cx, 42 + j * 11, center=True, small=True)        # 중심 42,53 → 바닥 ≤59


# ── 레벨업 축하 씬 ───────────────────────────────────────
class LevelUpScene(Scene):
    """레벨업 직후 '신남(excited)' 표정의 펫과 새 레벨/타이틀을 보여준다."""

    def __init__(self, level: int, title: str, return_scene: Scene) -> None:
        self.level = level
        self.title = title
        self.return_scene = return_scene

    def handle_input(self, actions, app) -> None:
        if actions:
            app.switch(self.return_scene)

    def render(self, ctx) -> None:
        ch = ctx.app.character
        _bg(ctx)
        # 표정을 'excited'로 강제해 축하 표정을 그린다(상태 무드와 무관).
        draw_pet(ctx, ch, ctx.width // 2, 18, scale=1.2, mood="excited")
        ctx.text("레벨 업!", ctx.width // 2, 42, color=config.COLOR_ACCENT,
                 big=True, center=True)
        label = f"Lv.{self.level}" + (f" {self.title}" if self.title else "")
        ctx.text(label, ctx.width // 2, 55, color=config.COLOR_FG,
                 center=True, small=True)


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


def _go(app, return_scene, popups, level_up=None) -> None:
    """레벨업 축하 → 팝업 → return_scene 순서로 이어 전환한다.

    level_up: 레벨업했다면 새 레벨(int), 아니면 None. 주어지면 '신남' 표정의
              LevelUpScene을 가장 먼저 보여준 뒤 나머지(팝업/복귀)로 이어진다.
    """
    target = return_scene
    if popups:
        target = PopupScene(popups, target)
    if level_up is not None:
        sfx.achievement(app.ctx)
        target = LevelUpScene(level_up, app.character.level_title(), target)
    app.switch(target)


def _grant_xp(app, return_scene, xp, popups) -> None:
    """XP를 적립하고 레벨업이면 축하 화면을 거쳐 전환한다(돌보기/탐험 공용)."""
    before, after = app.character.add_xp(xp)
    _go(app, return_scene, popups, level_up=after if after > before else None)


def _draw_level_hud(ctx, ch) -> None:
    """레벨 + XP 진행 바를 화면 '하단'에 앵커해 그린다.

    좌표를 ctx.height 기준으로 계산하므로 폰트/해상도가 바뀌어도 절대 화면 밖으로
    잘리지 않는다(예전 코인 표시가 잘리던 하단 영역).
    """
    lvl = ch.level()
    title = ch.level_title()
    _, _, ratio = ch.xp_progress()
    bar_h = 3
    bar_y = ctx.height - bar_h - 1          # 바닥에서 1px 위
    bar_x, bar_w = 4, 58
    fh = ctx.font_height(small=True)
    label = f"Lv.{lvl}" + (f" {title}" if title else "")
    ctx.text(label, bar_x, bar_y - fh - 1, color=config.COLOR_ACCENT, small=True)
    ctx.rect(bar_x, bar_y, bar_w, bar_h, config.COLOR_DIM, fill=False)
    fill_w = int(bar_w * ratio)
    if fill_w > 0:
        ctx.rect(bar_x, bar_y, fill_w, bar_h, config.COLOR_ACCENT, fill=True)


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
            ctx.text_bottom("아무 키나 누르세요", ctx.width // 2,
                            color=config.COLOR_DIM, center=True, small=True, margin=3)


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
        draw_pet(ctx, ch, 26, 26, scale=1.2)
        # 상단: 이름 + 재화. (진화 단계는 펫 외형으로 드러나므로 'Lv.' 텍스트는
        #  XP 레벨 전용으로 두고 여기선 표기하지 않는다 → 'Lv' 중복 제거)
        ctx.text(ch.name, 4, 2, color=config.COLOR_ACCENT, small=True)
        ctx.text(f"C:{ch.currency}", 40, 2, color=config.COLOR_WARN, small=True)
        # 우측 컬럼 전체 높이를 써서 6개 항목을 모두 표시(잘림/스크롤 없음).
        self.menu.render(ctx, x=66, y=2)
        # 하단: 레벨 + XP 진행 바 (높이 기준 앵커 → 절대 안 잘림)
        _draw_level_hud(ctx, ch)


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
        # 돌보기/훈련 XP 적립 (훈련은 라벨이 '…훈련'으로 끝난다)
        xp = config.XP_REWARDS["train"] if label.endswith("훈련") else config.XP_REWARDS["care"]
        # 훈련으로 능력치 임계값을 넘으면 업적이 해금될 수 있다.
        _grant_xp(app, self, xp, _progress_popups(app))

    def render(self, ctx) -> None:
        ch = ctx.app.character
        _bg(ctx)
        draw_pet(ctx, ch, 100, 18, scale=0.8)
        ctx.text(mood_label(ch), 78, 30, color=config.COLOR_DIM, small=True)
        self.menu.render(ctx, x=2, y=2)
        # 우측 스탯 2줄 — 작은 폰트로 화면 안에 들어오게(y=40,52 → 바닥 64 이내).
        ctx.text(f"포{ch.fullness} 청{ch.cleanliness}", 70, 40,
                 color=config.COLOR_DIM, small=True)
        ctx.text(f"행{ch.happiness} 스{ch.stress}", 70, 52,
                 color=config.COLOR_DIM, small=True)


# ── 미니게임 선택 씬 ─────────────────────────────────────
class MiniGameMenuScene(Scene):
    _GAMES = ["오목", "가위바위보", "스네이크", "초음파 점프", "색깔 찾기",
              "두더지 잡기", "뒤로"]

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
        self.menu.render(ctx, y=13)
        if self.last_reward:
            name, reward = self.last_reward
            ctx.text_bottom(f"+{reward} ({name})", 6,
                            color=config.COLOR_WARN, small=True)


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
        self.menu.render(ctx, y=20)


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
        self.menu.render(ctx, x=4, y=13)
        if self.msg:
            ctx.text_bottom(self.msg, 4, color=config.COLOR_WARN, small=True)


# ── 업적 씬 ──────────────────────────────────────────────
class AchievementScene(Scene):
    def __init__(self) -> None:
        self.scroll = 0

    _VISIBLE = 4   # 한 화면에 보이는 업적 줄 수(작은 폰트 12px 기준, 화면 안에 들어옴)

    def handle_input(self, actions, app) -> None:
        total = len(config.ACHIEVEMENTS)
        for a in actions:
            if a == "down":
                self.scroll = min(self.scroll + 1, max(0, total - self._VISIBLE))
            elif a == "up":
                self.scroll = max(self.scroll - 1, 0)
            elif a == "b":
                app.switch(MenuScene())

    def render(self, ctx) -> None:
        ch = ctx.app.character
        _bg(ctx)
        ctx.text("업적", 6, 2, color=config.COLOR_ACCENT, small=True)
        rows = achievements.all_with_status(ch)
        for i, (ach, owned) in enumerate(rows[self.scroll:self.scroll + self._VISIBLE]):
            mark = "★" if owned else "☆"
            color = config.COLOR_ACCENT if owned else config.COLOR_DIM
            ctx.text(f"{mark} {ach['title']}", 4, 16 + i * 12, color=color, small=True)


# ── 엔딩 씬 ──────────────────────────────────────────────
class EndingScene(Scene):
    def handle_input(self, actions, app) -> None:
        if actions:
            app.switch(MenuScene())

    def render(self, ctx) -> None:
        ch = ctx.app.character
        ending = determine_ending(ch)
        _bg(ctx)
        draw_pet(ctx, ch, ctx.width // 2, 12, scale=0.8)
        ctx.text(ending["title"], ctx.width // 2, 26,
                 color=config.COLOR_ACCENT, big=True, center=True)
        # 본문은 작은 폰트로 최대 2줄(y=40,51 → 바닥 64 이내).
        for i, line in enumerate(_wrap(ending["desc"], 20)[:2]):
            ctx.text(line, ctx.width // 2, 40 + i * 11, center=True, small=True)


# ── 미니게임 실행 + 보상/이벤트/업적 처리 ────────────────
def play_and_reward(app, return_scene, name, difficulty="normal") -> int:
    """미니게임을 실행하고 보상·통계·이벤트·업적까지 처리한 뒤 전환한다."""
    ctx = app.ctx
    reward = run_minigame(name, ctx, difficulty)
    ch = app.character
    ch.currency += reward
    ch.total_earned += reward
    ch.games_played += 1
    # XP: 참가 기본 + 승리(보상>0) 보너스
    xp = config.XP_REWARDS["minigame_play"]
    if reward > 0:
        xp += config.XP_REWARDS["minigame_win"]
        sfx.win(ctx)
    before, after = ch.add_xp(xp)
    if hasattr(return_scene, "last_reward"):
        return_scene.last_reward = (name, reward)
    ev = events.maybe_trigger(ch, app.rng)
    _go(app, return_scene, _progress_popups(app, before_event=ev),
        level_up=after if after > before else None)
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
        if name == "두더지 잡기":
            return WhackAMole(ctx=ctx).play()
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
