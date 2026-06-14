"""게임 컨텍스트 — 입력·렌더·시간·하드웨어를 한곳에서 추상화한다.

씬과 미니게임은 pygame이나 하드웨어를 직접 만지지 않고 이 객체만 사용한다.
덕분에 PC(키보드)·라즈베리파이(조이스틱+OLED)·헤드리스(테스트) 모두에서
같은 코드가 돈다.

행동(action) 문자열: 'up' 'down' 'left' 'right' 'a'(확인) 'b'(취소)
"""
import os

from .. import config

# 헤드리스 모드면 창/사운드 없이 동작하도록 SDL 더미 드라이버 지정 (pygame import 전에).
if config.HEADLESS:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402  (SDL 환경변수 설정 후 임포트해야 함)

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
        self.font = pygame.font.SysFont(None, 11)
        self.font_big = pygame.font.SysFont(None, 18)

        if not self.headless:
            scale = config.WINDOW_SCALE
            self.window = pygame.display.set_mode(
                (self.width * scale, self.height * scale))
            pygame.display.set_caption("RasPet")
        else:
            self.window = None

        self.clock = pygame.time.Clock()
        self._actions: set[str] = set()
        self._prev_dir = "center"   # 조이스틱 엣지 검출용

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
        """그린 프레임을 창과 OLED로 내보낸다."""
        if self.window is not None:
            scaled = pygame.transform.scale(self.surface, self.window.get_size())
            self.window.blit(scaled, (0, 0))
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
