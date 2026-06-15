"""캐릭터 스프라이트 — 외부 에셋 없이 도형으로 펫을 그린다.

성장 단계(stage)에 따라 외형이 달라지고(알→아기→어린이→어른),
무드(mood)에 따라 표정이 바뀐다. (로드맵 6단계: 진화·감정 표현)
"""
from collections import namedtuple

import pygame

from .. import config
from ..character.mood import compute_mood

_DARK = (40, 40, 55)


def draw_pet(ctx, character, cx, cy, scale=1.0, mood=None) -> None:
    """(cx, cy)를 중심으로 캐릭터를 그린다.

    mood를 직접 넘기면 그 표정으로 그린다(예: 레벨업 축하의 'excited').
    생략하면 캐릭터 상태로부터 계산한다.
    """
    stage = max(0, min(character.stage, 3))
    color = config.STAGE_COLORS[stage]
    if stage == 0:
        _draw_egg(ctx, cx, cy, scale, color)
        return
    if mood is None:
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


# 얼굴 도형 좌표 묶음 — 모든 표정이 같은 기준점을 쓰도록 한곳에서 계산한다.
# 모든 좌표는 중심(cx,cy)과 반지름 r로부터 나오므로 항상 몸(원) 안에 들어온다.
_Geom = namedtuple("_Geom", "cx cy r lx rx eye_y er mouth_y")


def _geom(cx, cy, r) -> "_Geom":
    eye_dx = r * 0.42
    return _Geom(cx=cx, cy=cy, r=r,
                 lx=cx - eye_dx, rx=cx + eye_dx,
                 eye_y=cy - r * 0.12, er=max(1, int(r * 0.13)),
                 mouth_y=cy + r * 0.45)


def _draw_face(ctx, cx, cy, r, mood) -> None:
    """무드 id에 해당하는 얼굴을 그린다. 모르는 무드는 neutral로 폴백한다.

    새 표정을 추가하려면 함수 하나를 만들고 _FACES에 등록하면 된다
    (config.MOODS에 규칙을 더하는 것과 짝).
    """
    _FACES.get(mood, _face_neutral)(ctx, _geom(cx, cy, r))


# ── 개별 표정 (눈·입 변형 중심의 단순 도형) ─────────────
def _eyes_dots(ctx, g, dy=0) -> None:
    ctx.circle(g.lx, g.eye_y + dy, g.er, _DARK)
    ctx.circle(g.rx, g.eye_y + dy, g.er, _DARK)


def _face_neutral(ctx, g) -> None:
    _eyes_dots(ctx, g)
    ctx.line(g.cx - g.r * 0.25, g.mouth_y, g.cx + g.r * 0.25, g.mouth_y, _DARK)


def _face_happy(ctx, g) -> None:
    _eyes_dots(ctx, g)
    _smile(ctx, g.cx, g.mouth_y, g.r, up=True)


def _face_sad(ctx, g) -> None:
    _eyes_dots(ctx, g, dy=1)
    _smile(ctx, g.cx, g.mouth_y + 1, g.r, up=False)


def _face_sick(ctx, g) -> None:
    _x_eye(ctx, g.lx, g.eye_y, g.er)
    _x_eye(ctx, g.rx, g.eye_y, g.er)
    ctx.line(g.cx - g.r * 0.3, g.mouth_y, g.cx + g.r * 0.3, g.mouth_y, _DARK)


def _face_hungry(ctx, g) -> None:
    _eyes_dots(ctx, g)
    ctx.circle(g.cx, g.mouth_y, max(1, int(g.r * 0.18)), _DARK, fill=False)


def _face_stressed(ctx, g) -> None:
    # 화난 눈썹 + 일자입
    ctx.line(g.lx - g.er, g.eye_y - g.er, g.lx + g.er, g.eye_y, _DARK)
    ctx.line(g.rx + g.er, g.eye_y - g.er, g.rx - g.er, g.eye_y, _DARK)
    _eyes_dots(ctx, g, dy=1)
    ctx.line(g.cx - g.r * 0.3, g.mouth_y, g.cx + g.r * 0.3, g.mouth_y, _DARK)


def _face_dirty(ctx, g) -> None:
    _eyes_dots(ctx, g)
    ctx.line(g.cx - g.r * 0.25, g.mouth_y, g.cx + g.r * 0.25, g.mouth_y, _DARK)
    # 얼룩
    ctx.circle(g.cx + g.r * 0.5, g.cy + g.r * 0.2, max(1, int(g.r * 0.12)),
               config.COLOR_WARN)


def _face_lonely(ctx, g) -> None:
    # 바깥쪽으로 처진 눈 + 작은 점입 + 눈물 한 방울
    ctx.line(g.lx - g.er, g.eye_y - g.er, g.lx + g.er, g.eye_y + g.er, _DARK)
    ctx.line(g.rx - g.er, g.eye_y + g.er, g.rx + g.er, g.eye_y - g.er, _DARK)
    ctx.circle(g.cx, g.mouth_y, max(1, int(g.r * 0.1)), _DARK)
    ctx.circle(g.rx, g.eye_y + g.er * 2, max(1, int(g.r * 0.12)), config.COLOR_ACCENT)


def _face_sleepy(ctx, g) -> None:
    # 감은 눈(─ ─) + 작은 입 + 'z'
    ctx.line(g.lx - g.er, g.eye_y, g.lx + g.er, g.eye_y, _DARK)
    ctx.line(g.rx - g.er, g.eye_y, g.rx + g.er, g.eye_y, _DARK)
    ctx.circle(g.cx, g.mouth_y, max(1, int(g.r * 0.1)), _DARK)
    ctx.text("z", g.rx, g.eye_y - g.r * 0.7, color=_DARK, small=True)


def _face_excited(ctx, g) -> None:
    # 반짝이는 눈(^ ^) + 크게 벌린 입 → 레벨업 축하용 '신남'
    ctx.line(g.lx - g.er, g.eye_y, g.lx, g.eye_y - g.er, _DARK)
    ctx.line(g.lx, g.eye_y - g.er, g.lx + g.er, g.eye_y, _DARK)
    ctx.line(g.rx - g.er, g.eye_y, g.rx, g.eye_y - g.er, _DARK)
    ctx.line(g.rx, g.eye_y - g.er, g.rx + g.er, g.eye_y, _DARK)
    ctx.circle(g.cx, g.mouth_y, max(2, int(g.r * 0.22)), _DARK)


def _face_asleep(ctx, g) -> None:
    # 푹 잠든 표정: 감은 눈(─ ─) + 작은 입 + 큼직한 'Z'들
    ctx.line(g.lx - g.er, g.eye_y, g.lx + g.er, g.eye_y, _DARK)
    ctx.line(g.rx - g.er, g.eye_y, g.rx + g.er, g.eye_y, _DARK)
    ctx.circle(g.cx, g.mouth_y, max(1, int(g.r * 0.1)), _DARK)
    ctx.text("Z", g.rx + g.er, g.eye_y - g.r * 0.6, color=_DARK, small=True)
    ctx.text("z", g.rx + g.er * 2, g.eye_y - g.r * 1.1, color=_DARK, small=True)


def _face_hot(ctx, g) -> None:
    # 더위: 축 처진 눈 + 혀 내민 입 + 땀방울
    _eyes_dots(ctx, g, dy=1)
    ctx.circle(g.cx, g.mouth_y + 1, max(1, int(g.r * 0.16)), _DARK, fill=False)
    ctx.line(g.cx, g.mouth_y, g.cx, g.mouth_y + g.r * 0.35, config.COLOR_WARN)  # 혀
    ctx.circle(g.lx - g.er * 2, g.eye_y, max(1, int(g.r * 0.12)), config.COLOR_ACCENT)  # 땀


def _face_cold(ctx, g) -> None:
    # 추위: 움츠린 눈 + 떨리는 입(지그재그)
    _eyes_dots(ctx, g)
    w = g.r * 0.3
    y = g.mouth_y
    ctx.line(g.cx - w, y, g.cx - w * 0.33, y - 2, _DARK)
    ctx.line(g.cx - w * 0.33, y - 2, g.cx + w * 0.33, y + 2, _DARK)
    ctx.line(g.cx + w * 0.33, y + 2, g.cx + w, y - 2, _DARK)


_FACES = {
    "neutral": _face_neutral, "happy": _face_happy, "sad": _face_sad,
    "sick": _face_sick, "hungry": _face_hungry, "stressed": _face_stressed,
    "dirty": _face_dirty, "lonely": _face_lonely, "sleepy": _face_sleepy,
    "excited": _face_excited, "asleep": _face_asleep,
    "hot": _face_hot, "cold": _face_cold,
}


def _smile(ctx, cx, y, r, up=True) -> None:
    w = r * 0.3
    dy = 2 if up else -2
    ctx.line(cx - w, y, cx, y + dy, _DARK)
    ctx.line(cx, y + dy, cx + w, y, _DARK)


def _x_eye(ctx, x, y, er) -> None:
    ctx.line(x - er, y - er, x + er, y + er, _DARK)
    ctx.line(x - er, y + er, x + er, y - er, _DARK)
