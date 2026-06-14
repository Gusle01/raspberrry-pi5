"""게임 컨텍스트 — 입력·렌더·시간·하드웨어를 한곳에서 추상화한다.

씬과 미니게임은 pygame이나 하드웨어를 직접 만지지 않고 이 객체만 사용한다.
덕분에 PC(키보드)·라즈베리파이(조이스틱+OLED)·헤드리스(테스트) 모두에서
같은 코드가 돈다.

행동(action) 문자열: 'up' 'down' 'left' 'right' 'a'(확인) 'b'(취소)
"""
import os
import sys

from .. import config

# 헤드리스 모드면 창/사운드 없이 동작하도록 SDL 더미 드라이버 지정 (pygame import 전에).
if config.HEADLESS:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import glob  # noqa: E402

import pygame  # noqa: E402  (SDL 환경변수 설정 후 임포트해야 함)

# 한글 폰트 파일을 직접 찾을 때 훑어볼 경로 패턴
_FONT_GLOBS = [
    "/usr/share/fonts/**/NotoSansCJK*.ttc",
    "/usr/share/fonts/**/Nanum*.ttf",
    "/usr/share/fonts/**/Un*.ttf",
    "/usr/share/fonts/**/*Gothic*.tt?",
]


def resolve_korean_font_path() -> str | None:
    """한글 글리프가 있는 폰트 파일 경로를 찾는다. 못 찾으면 None."""
    if config.FONT_PATH and os.path.exists(config.FONT_PATH):
        return config.FONT_PATH
    for family in config.FONT_CANDIDATES:          # 폰트 패밀리 이름으로 탐색
        path = pygame.font.match_font(family)
        if path:
            return path
    for pattern in _FONT_GLOBS:                     # 파일 경로 직접 탐색
        hits = sorted(glob.glob(pattern, recursive=True))
        if hits:
            return hits[0]
    return None


def load_font(path: str | None, size: int):
    """폰트를 로드한다. 경로가 없거나 실패하면 기본 폰트(라틴 전용)로 폴백."""
    if path:
        try:
            return pygame.font.Font(path, size)
        except Exception:
            pass
    return pygame.font.SysFont(None, size)


# 키보드 → 행동 매핑 (PC 개발용)
_KEYMAP = {
    pygame.K_UP: "up", pygame.K_w: "up",
    pygame.K_DOWN: "down", pygame.K_s: "down",
    pygame.K_LEFT: "left", pygame.K_a: "left",
    pygame.K_RIGHT: "right", pygame.K_d: "right",
    pygame.K_RETURN: "a", pygame.K_SPACE: "a", pygame.K_z: "a",
    pygame.K_ESCAPE: "b", pygame.K_BACKSPACE: "b", pygame.K_x: "b",
}


class GameContext:
    """입력/출력/하드웨어 게이트웨이."""

    def __init__(self, hardware=None, headless=None, script=None) -> None:
        """
        Args:
            hardware: dict(display, joystick, ultrasonic, buzzer, camera, hand)
            headless: 창 없이 동작(기본은 config.HEADLESS)
            script: 자동 진행용 행동 시퀀스(list[set[str]]). 주어지면 키 입력 대신
                    프레임마다 하나씩 소비하고, 모두 소진되면 종료한다(테스트용).
        """
        self.hw = hardware or {}
        self.headless = config.HEADLESS if headless is None else headless
        self._script = list(script) if script is not None else None
        self.running = True

        self.width = config.SCREEN_WIDTH
        self.height = config.SCREEN_HEIGHT

        pygame.init()
        self.surface = pygame.Surface((self.width, self.height))
        self.font_path = resolve_korean_font_path()
        if self.font_path is None:
            print("[RasPet] 한글 폰트를 찾지 못했습니다. 글자가 깨지면 "
                  "'sudo apt install -y fonts-noto-cjk' 또는 fonts-nanum 설치 후 다시 실행하세요.",
                  file=sys.stderr)
        self.font = load_font(self.font_path, config.FONT_SIZE)
        self.font_big = load_font(self.font_path, config.FONT_SIZE_BIG)

        self._fullscreen = config.FULLSCREEN
        self.window = None
        if not self.headless:
            self._create_window()
            pygame.display.set_caption("RasPet")

        self.clock = pygame.time.Clock()
        self._actions: set[str] = set()
        self._prev_dir = "center"   # 조이스틱 엣지 검출용

    # ── 창 관리 ─────────────────────────────────────────
    def _create_window(self) -> None:
        """현재 모드(전체화면/창)에 맞게 표시 창을 만든다."""
        if self._fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            flags = pygame.RESIZABLE if config.WINDOW_RESIZABLE else 0
            self.window = pygame.display.set_mode(
                (self.width * config.WINDOW_SCALE,
                 self.height * config.WINDOW_SCALE), flags)

    def toggle_fullscreen(self) -> None:
        self._fullscreen = not self._fullscreen
        self._create_window()

    # ── 입력 ────────────────────────────────────────────
    def poll(self) -> set[str]:
        """이번 프레임에 새로 발생한 행동 집합을 수집해 반환한다(엣지 트리거)."""
        self._actions = set()

        if self._script is not None:
            # 스크립트 모드: 프레임당 한 묶음 소비
            if self._script:
                self._actions = set(self._script.pop(0))
            else:
                self.running = False
            return self._actions

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE and not self._fullscreen:
                self.window = pygame.display.set_mode(
                    event.size,
                    pygame.RESIZABLE if config.WINDOW_RESIZABLE else 0)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.toggle_fullscreen()
            elif event.type == pygame.KEYDOWN and event.key in _KEYMAP:
                self._actions.add(_KEYMAP[event.key])

        # 조이스틱(있으면): 방향이 center→non-center로 바뀌는 순간만 행동으로
        joy = self.hw.get("joystick")
        if joy is not None and getattr(joy, "available", False):
            d = joy.direction()
            if d != "center" and d != self._prev_dir:
                self._actions.add(d)
            if d == "center" and joy.pressed():
                self._actions.add("a")
            self._prev_dir = d

        return self._actions

    @property
    def actions(self) -> set[str]:
        return self._actions

    def wait_action(self, valid=None) -> str | None:
        """valid 중 하나가 입력될 때까지(또는 종료까지) 기다렸다 반환한다."""
        while self.running:
            for a in self.poll():
                if valid is None or a in valid:
                    return a
            self.present()
            self.tick()
        return None

    # ── 시간 ────────────────────────────────────────────
    def tick(self) -> float:
        """FPS를 제한하고 경과 시간(초)을 반환한다."""
        return self.clock.tick(config.FPS) / 1000.0

    # ── 렌더 ────────────────────────────────────────────
    def clear(self, color=config.COLOR_BG) -> None:
        self.surface.fill(color)

    def text(self, s, x, y, color=config.COLOR_FG, big=False, center=False) -> None:
        font = self.font_big if big else self.font
        img = font.render(str(s), True, color)
        if center:
            rect = img.get_rect(center=(x, y))
            self.surface.blit(img, rect)
        else:
            self.surface.blit(img, (x, y))

    def rect(self, x, y, w, h, color, fill=True) -> None:
        pygame.draw.rect(self.surface, color, (x, y, w, h), 0 if fill else 1)

    def circle(self, x, y, r, color, fill=True) -> None:
        pygame.draw.circle(self.surface, color, (int(x), int(y)), int(r),
                           0 if fill else 1)

    def line(self, x1, y1, x2, y2, color, width=1) -> None:
        pygame.draw.line(self.surface, color, (x1, y1), (x2, y2), width)

    def present(self) -> None:
        """그린 프레임을 창과 OLED로 내보낸다.

        창에는 가로세로 비율을 유지한 채 최대한 크게(레터박스) 그려 찌그러짐을 막는다.
        """
        if self.window is not None:
            win_w, win_h = self.window.get_size()
            scale = min(win_w / self.width, win_h / self.height)
            sw, sh = int(self.width * scale), int(self.height * scale)
            scaled = pygame.transform.scale(self.surface, (sw, sh))
            self.window.fill((0, 0, 0))   # 남는 영역(레터박스)은 검정
            self.window.blit(scaled, ((win_w - sw) // 2, (win_h - sh) // 2))
            pygame.display.flip()
        display = self.hw.get("display")
        if display is not None and getattr(display, "available", False):
            display.show(self._to_pil())

    def _to_pil(self):
        """현재 surface를 PIL 이미지로 변환한다(OLED 전송용)."""
        from PIL import Image
        raw = pygame.image.tostring(self.surface, "RGB")
        return Image.frombytes("RGB", (self.width, self.height), raw)

    # ── 하드웨어 단축 접근 ───────────────────────────────
    def beep(self, freq=880, duration=0.05) -> None:
        bz = self.hw.get("buzzer")
        if bz is not None:
            bz.beep(freq, duration)

    def distance_cm(self) -> float:
        u = self.hw.get("ultrasonic")
        return u.distance_cm() if u is not None else config.JUMP_DISTANCE_MAX_CM

    def capture_frame(self):
        cam = self.hw.get("camera")
        return cam.capture_frame() if cam is not None else None

    def classify_hand(self):
        hand = self.hw.get("hand")
        if hand is None:
            return None
        return hand.classify_gesture(self.capture_frame())

    def quit(self) -> None:
        pygame.quit()
