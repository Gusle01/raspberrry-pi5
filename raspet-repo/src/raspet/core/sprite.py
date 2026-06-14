"""캐릭터 스프라이트 — 외부 에셋 없이 도형으로 펫을 그린다.

성장 단계(stage)에 따라 외형이 달라지고(알→아기→어린이→어른),
무드(mood)에 따라 표정이 바뀐다. (로드맵 6단계: 진화·감정 표현)
"""
import pygame

from .. import config
from ..character.mood import compute_mood

_DARK = (40, 40, 55)


def draw_pet(ctx, character, cx, cy, scale=1.0) -> None:
    """(cx, cy)를 중심으로 캐릭터를 그린다."""
    stage = max(0, min(character.stage, 3))
    color = config.STAGE_COLORS[stage]
    if stage == 0:
        _draw_egg(ctx, cx, cy, scale, color)
        return
    mood = compute_mood(character)
    r = int((7 + stage * 3) * scale)
    # 단계별 장식: 귀(2단계+), 발(3단계)
    if stage >= 2:
        ctx.circle(cx - r * 0.6, cy - r * 0.8, max(2, r * 0.3), color)
        ctx.circle(cx + r * 0.6, cy - r * 0.8, max(2, r * 0.3), color)
    ctx.circle(cx, cy, r, color)
    if stage >= 3:
        ctx.circle(cx - r * 0.5, cy + r * 0.9, max(2, r * 0.25), color)
        ctx.circle(cx + r * 0.5, cy + r * 0.9, max(2, r * 0.25), color)
    _draw_face(ctx, cx, cy, r, mood)


def _draw_egg(ctx, cx, cy, scale, color) -> None:
    w = int(12 * scale)
    h = int(16 * scale)
    rect = (int(cx - w / 2), int(cy - h / 2), w, h)
    pygame.draw.ellipse(ctx.surface, color, rect)
    # 갈라진 금
    midy = int(cy)
    ctx.line(cx - w / 2, midy, cx - w / 6, midy - 2, _DARK)
    ctx.line(cx - w / 6, midy - 2, cx + w / 8, midy + 2, _DARK)
    ctx.line(cx + w / 8, midy + 2, cx + w / 2, midy - 1, _DARK)


def _draw_face(ctx, cx, cy, r, mood) -> None:
    eye_dx = r * 0.42
    eye_y = cy - r * 0.12
    er = max(1, int(r * 0.13))
    lx, rx = cx - eye_dx, cx + eye_dx
    mouth_y = cy + r * 0.45

    if mood == "happy":
        ctx.circle(lx, eye_y, er, _DARK)
        ctx.circle(rx, eye_y, er, _DARK)
        _smile(ctx, cx, mouth_y, r, up=True)
    elif mood == "sad":
        ctx.circle(lx, eye_y + 1, er, _DARK)
        ctx.circle(rx, eye_y + 1, er, _DARK)
        _smile(ctx, cx, mouth_y + 1, r, up=False)
    elif mood == "sick":
        _x_eye(ctx, lx, eye_y, er)
        _x_eye(ctx, rx, eye_y, er)
        ctx.line(cx - r * 0.3, mouth_y, cx + r * 0.3, mouth_y, _DARK)
    elif mood == "hungry":
        ctx.circle(lx, eye_y, er, _DARK)
        ctx.circle(rx, eye_y, er, _DARK)
        ctx.circle(cx, mouth_y, max(1, int(r * 0.18)), _DARK, fill=False)
    elif mood == "stressed":
        # 화난 눈썹
        ctx.line(lx - er, eye_y - er, lx + er, eye_y, _DARK)
        ctx.line(rx + er, eye_y - er, rx - er, eye_y, _DARK)
        ctx.circle(lx, eye_y + 1, er, _DARK)
        ctx.circle(rx, eye_y + 1, er, _DARK)
        ctx.line(cx - r * 0.3, mouth_y, cx + r * 0.3, mouth_y, _DARK)
    elif mood == "dirty":
        ctx.circle(lx, eye_y, er, _DARK)
        ctx.circle(rx, eye_y, er, _DARK)
        ctx.line(cx - r * 0.25, mouth_y, cx + r * 0.25, mouth_y, _DARK)
        # 얼룩
        ctx.circle(cx + r * 0.5, cy + r * 0.2, max(1, int(r * 0.12)),
                   config.COLOR_WARN)
    else:  # neutral
        ctx.circle(lx, eye_y, er, _DARK)
        ctx.circle(rx, eye_y, er, _DARK)
        ctx.line(cx - r * 0.25, mouth_y, cx + r * 0.25, mouth_y, _DARK)


def _smile(ctx, cx, y, r, up=True) -> None:
    w = r * 0.3
    dy = 2 if up else -2
    ctx.line(cx - w, y, cx, y + dy, _DARK)
    ctx.line(cx, y + dy, cx + w, y, _DARK)


def _x_eye(ctx, x, y, er) -> None:
    ctx.line(x - er, y - er, x + er, y + er, _DARK)
    ctx.line(x - er, y + er, x + er, y - er, _DARK)
