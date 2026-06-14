"""효과음 — 부저로 짧은 멜로디를 낸다(없으면 무음). (로드맵 6단계)

ctx.beep을 통해 동작하므로 부저가 없으면 자동으로 아무 일도 일어나지 않는다.
"""


def _play(ctx, notes) -> None:
    for freq, dur in notes:
        ctx.beep(freq, dur)


def move(ctx) -> None:
    _play(ctx, [(523, 0.02)])


def confirm(ctx) -> None:
    _play(ctx, [(659, 0.03), (784, 0.03)])


def cancel(ctx) -> None:
    _play(ctx, [(392, 0.04)])


def win(ctx) -> None:
    _play(ctx, [(523, 0.05), (659, 0.05), (784, 0.08)])


def event(ctx) -> None:
    _play(ctx, [(700, 0.04), (900, 0.04)])


def achievement(ctx) -> None:
    _play(ctx, [(659, 0.05), (880, 0.05), (1047, 0.1)])
