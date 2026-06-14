"""가위바위보 (카메라 활용 · 필수).

카메라로 손을 촬영 → vision.hand 로 가위/바위/보 인식 →
컴퓨터의 무작위 선택과 비교해 승패 판정. (계획서 4.2.1 / 5.1)

손 인식을 못 쓰는 환경에서는 버튼(좌=바위/상=가위/우=보)으로 선택한다.
테스트에서는 choice_provider를 주입해 결정적으로 진행한다.
"""
import random

from .base import MiniGame
from .. import config

CHOICES = ("rock", "scissors", "paper")
_LABEL = {"rock": "바위", "scissors": "가위", "paper": "보"}
# 이긴다: key가 value를 이긴다
_BEATS = {"rock": "scissors", "scissors": "paper", "paper": "rock"}


def judge(user: str, com: str) -> str:
    """가위바위보 승패. 'win'(사람) / 'lose' / 'draw'."""
    if user == com:
        return "draw"
    return "win" if _BEATS[user] == com else "lose"


class RockPaperScissors(MiniGame):
    name = "가위바위보"

    def __init__(self, ctx=None, choice_provider=None, rng=None) -> None:
        self.ctx = ctx
        self.choice_provider = choice_provider
        self.rng = rng or random.Random()
        self.wins = 0
        self.losses = 0

    def play(self) -> int:
        """RPS_ROUNDS 라운드를 진행하고 획득 재화를 반환한다."""
        reward = 0
        for rnd in range(config.RPS_ROUNDS):
            user = self._get_user_choice()
            if user is None:                  # 종료/취소
                break
            com = self.rng.choice(CHOICES)
            result = judge(user, com)
            if result == "win":
                self.wins += 1
                reward += config.RPS_WIN_REWARD
            elif result == "lose":
                self.losses += 1
            self._show_round(rnd, user, com, result)
        # 매치 승리 보너스
        if self.wins > self.losses:
            reward += config.RPS_MATCH_BONUS
        return reward

    def _get_user_choice(self):
        """주입된 provider가 있으면 그걸, 없으면 상호작용 입력을 사용한다."""
        if self.choice_provider is not None:
            return self.choice_provider(self.ctx)
        return self._interactive_choice()

    def _interactive_choice(self):
        """손 인식이 가능하면 카메라로, 아니면 버튼으로 선택받는다."""
        ctx = self.ctx
        hand = ctx.hw.get("hand") if ctx else None
        if hand is not None and getattr(hand, "available", False):
            gesture = ctx.classify_hand()
            if gesture in CHOICES:
                return gesture
        # 버튼 선택: 좌=바위, 상=가위, 우=보
        if ctx is None:
            return None
        keymap = {"left": "rock", "up": "scissors", "right": "paper"}
        ctx.clear()
        ctx.text("가위바위보!", ctx.width // 2, 8, center=True)
        ctx.text("←바위 ↑가위 →보", ctx.width // 2, 30, center=True)
        action = ctx.wait_action(set(keymap) | {"b"})
        if action in keymap:
            return keymap[action]
        return None

    def _show_round(self, rnd, user, com, result):
        ctx = self.ctx
        if ctx is None:
            return
        msg = {"win": "이겼다!", "lose": "졌다...", "draw": "비김"}[result]
        ctx.clear()
        ctx.text(f"{rnd + 1}라운드", ctx.width // 2, 6, center=True)
        ctx.text(f"나:{_LABEL[user]}  컴:{_LABEL[com]}", ctx.width // 2, 26, center=True)
        ctx.text(msg, ctx.width // 2, 44, color=config.COLOR_ACCENT,
                 big=True, center=True)
        ctx.present()
        ctx.wait_action({"a", "b"})
