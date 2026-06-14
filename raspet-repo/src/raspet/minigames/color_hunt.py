"""카메라 색깔 찾기 (제안).

제시된 색을 띤 주변 사물을 카메라에 비추면 OpenCV 색상 인식으로 판정.
(계획서 4.2.5)

색 검출(color_match)은 OpenCV가 있을 때만 동작하며, 없거나 테스트 시에는
detector를 주입해 대체할 수 있다.
"""
import random

from .base import MiniGame
from .. import config

try:
    import cv2
    import numpy as np
    _CV_AVAILABLE = True
except Exception:
    _CV_AVAILABLE = False


def color_match(frame, lower, upper, threshold: float = 0.05) -> bool:
    """프레임에서 [lower, upper] HSV 범위 픽셀 비율이 threshold 이상이면 True."""
    if frame is None or not _CV_AVAILABLE:
        return False
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, tuple(lower), tuple(upper))
    ratio = float(np.count_nonzero(mask)) / mask.size
    return ratio >= threshold


class ColorHunt(MiniGame):
    name = "색깔 찾기"

    def __init__(self, ctx=None, detector=None, rng=None) -> None:
        self.ctx = ctx
        self.rng = rng or random.Random()
        self.targets = list(config.COLOR_HUNT_TARGETS)
        # detector(frame, target_tuple) -> bool. 기본은 OpenCV color_match.
        self.detector = detector or self._default_detector
        self.found = 0

    def _default_detector(self, frame, target) -> bool:
        _, lower, upper = target
        return color_match(frame, lower, upper)

    def play(self) -> int:
        ctx = self.ctx
        if ctx is None:
            return 0
        reward = 0
        for _ in range(config.COLOR_HUNT_ROUNDS):
            target = self.rng.choice(self.targets)
            if self._run_round(target):
                self.found += 1
                reward += config.COLOR_HUNT_REWARD_PER_ROUND
            if not ctx.running:
                break
        return reward

    def _run_round(self, target) -> bool:
        """한 라운드: 제한 시간 안에 목표 색을 비추면 True."""
        ctx = self.ctx
        name = target[0]
        elapsed = 0.0
        while ctx.running and elapsed < config.COLOR_HUNT_TIME_LIMIT_S:
            for a in ctx.poll():
                if a == "b":
                    return False
            elapsed += ctx.tick()
            frame = ctx.capture_frame()
            if self.detector(frame, target):
                self._flash(name, True)
                return True
            ctx.clear()
            ctx.text("이 색을 찾아라!", ctx.width // 2, 10, center=True)
            ctx.text(name, ctx.width // 2, 30, color=config.COLOR_ACCENT,
                     big=True, center=True)
            remain = max(0, int(config.COLOR_HUNT_TIME_LIMIT_S - elapsed))
            ctx.text(f"{remain}s", ctx.width - 16, 2, color=config.COLOR_DIM)
            ctx.present()
        self._flash(name, False)
        return False

    def _flash(self, name, ok) -> None:
        ctx = self.ctx
        ctx.clear()
        msg = "찾았다!" if ok else "시간 초과"
        color = config.COLOR_ACCENT if ok else config.COLOR_WARN
        ctx.text(msg, ctx.width // 2, ctx.height // 2, color=color,
                 big=True, center=True)
        ctx.present()
