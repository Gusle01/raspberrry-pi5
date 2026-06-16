"""가위바위보 (카메라 활용 · 필수).

카메라로 손을 촬영 → vision.hand 로 가위/바위/보 인식 →
컴퓨터의 무작위 선택과 비교해 승패 판정. (계획서 4.2.1 / 5.1)

손 인식을 못 쓰는 환경에서는 버튼(좌=바위/상=가위/우=보)으로 선택한다.
테스트에서는 choice_provider를 주입해 결정적으로 진행한다.
"""
import math
import random

from .base import MiniGame
from .. import config
from ..vision.hand import majority_gesture

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
        if ctx is None:
            return None
        hand = ctx.hw.get("hand")
        if hand is not None and getattr(hand, "available", False):
            gesture = self._camera_choice(hand)
            if gesture in CHOICES:
                return gesture
        # 버튼 선택: 좌=바위, 상=가위, 우=보
        keymap = {"left": "rock", "up": "scissors", "right": "paper"}
        ctx.clear()
        ctx.text("가위바위보!", ctx.width // 2, 8, center=True)
        ctx.text("←바위 ↑가위 →보", ctx.width // 2, 30, center=True)
        action = ctx.wait_action(set(keymap) | {"b"})
        if action in keymap:
            return keymap[action]
        return None

    def _camera_choice(self, hand):
        """영상 미리보기를 띄운 채 카운트다운하다가, 0이 되는 순간 프레임을 캡처해 판정한다.

        RPS_CAMERA_SECONDS 동안 실시간 영상을 보여주며 카운트다운(5·4·3·2·1)을 하고,
        그동안 인식되는 손은 화면에 미리보기로만 띄운다(즉시 확정하지 않음). 카운트다운이
        끝나는 순간 찍힌 프레임의 손 모양을 최종 선택으로 확정한다. 인식 실패 시 None을
        돌려준다(호출부가 버튼 선택으로 폴백). 'b'로 취소 가능.
        """
        ctx = self.ctx
        total = config.RPS_CAMERA_SECONDS
        elapsed = 0.0
        gesture = None
        last_shown = None
        while ctx.running and elapsed < total:
            for a in ctx.poll():
                if a == "b":
                    return None
            elapsed += ctx.tick()
            frame = ctx.capture_frame()
            gesture = hand.classify_gesture(frame)   # 미리보기용(아직 확정 아님)
            remain = max(1, math.ceil(total - elapsed))
            if remain != last_shown:                 # 매 초 카운트다운 효과음
                ctx.beep(freq=660, duration=0.04)
                last_shown = remain
            ctx.show_camera(frame, label=f"{remain}...")
            ctx.clear()
            ctx.text("준비! 카메라를 봐", ctx.width // 2, 6, center=True)
            ctx.text(str(remain), ctx.width // 2, 26,
                     color=config.COLOR_ACCENT, big=True, center=True)
            ctx.text(f"({_LABEL.get(gesture, '...')})", ctx.width // 2, 52,
                     color=config.COLOR_DIM, center=True)
            ctx.seg_show_seconds(remain)             # 7세그먼트: 남은 시간
            ctx.present()

        # 카운트다운 종료 → "찰칵!" 여러 프레임을 모아 다수결로 최종 확정한다.
        # 단일 프레임은 흔들림/노이즈로 오인식하기 쉬우므로 짧은 구간을 표본화한다.
        ctx.beep(freq=1320, duration=0.08)           # 셔터음
        votes = []
        first_frame = None
        for i in range(config.RPS_CAPTURE_SAMPLES):
            if not ctx.running:
                break
            frame = ctx.capture_frame()
            if first_frame is None:
                first_frame = frame
            votes.append(hand.classify_gesture(frame))
            ctx.tick()                               # 프레임 간 간격 확보(FPS 제한)
        final = majority_gesture(votes)
        ctx.show_camera(first_frame, label="찰칵!")
        ctx.clear()
        ctx.text("찰칵!", ctx.width // 2, 8, color=config.COLOR_ACCENT,
                 big=True, center=True)
        ctx.text(_LABEL.get(final, "인식 실패"), ctx.width // 2, 40,
                 center=True)
        ctx.present()
        # 캡처 결과를 잠깐 보여준다(약 0.7초).
        hold = 0.0
        while ctx.running and hold < 0.7:
            ctx.poll()
            hold += ctx.tick()
        return final if final in CHOICES else None

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
