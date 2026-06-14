"""캐릭터 데이터 모델과 능력치(스탯) 시스템."""
from dataclasses import dataclass, field, asdict

from .. import config
from . import progression

# 엔딩/진화 판정에 쓰이는 핵심 능력치
CORE_STATS = ("strength", "intellect", "charm", "sensitivity")
# 0~STAT_MAX 범위로 제한되는 모든 수치 필드 (재화·인벤토리·이름·단계 제외)
CLAMPED_FIELDS = ("health", "strength", "intellect", "charm",
                  "sensitivity", "stress", "happiness", "fullness", "cleanliness")


def _clamp(value: int) -> int:
    return max(0, min(config.STAT_MAX, int(value)))


@dataclass
class Character:
    """육성 대상 캐릭터.

    계획서 4.1.1의 능력치 구성을 따른다.
    """
    name: str = "Pet"
    # 능력치 (0~config.STAT_MAX)
    health: int = 50        # 체력
    strength: int = 10      # 근력
    intellect: int = 10     # 지력
    charm: int = 10         # 매력
    sensitivity: int = 10   # 감수성
    stress: int = 0         # 스트레스 (낮을수록 좋음)
    happiness: int = 50     # 행복도
    # 돌봄 상태 (시간에 따라 감소 → needs.py)
    fullness: int = 100     # 포만도
    cleanliness: int = 100  # 청결도
    # 진행
    currency: int = 0       # 재화
    inventory: list = field(default_factory=list)
    stage: int = 0          # 성장 단계(진화: 누적 능력치 기반)
    xp: int = 0             # 누적 경험치(전체 진행도 레이어 → 레벨은 여기서 파생)
    # 통계/도전 과제
    games_played: int = 0           # 미니게임 플레이 횟수
    total_earned: int = 0           # 누적 획득 재화
    achievements: list = field(default_factory=list)  # 달성한 업적 id 목록

    def grow(self, stat: str, amount: int) -> int:
        """능력치를 올린다 (상한·스트레스 효율 적용). 실제 증가량을 반환한다.

        스트레스가 STRESS_PENALTY_THRESHOLD 이상이면 성장 효율이 떨어진다.
        """
        if stat not in CLAMPED_FIELDS:
            raise ValueError(f"알 수 없는 능력치: {stat}")
        factor = (config.STRESS_PENALTY_FACTOR
                  if self.stress >= config.STRESS_PENALTY_THRESHOLD else 1.0)
        before = getattr(self, stat)
        after = _clamp(before + round(amount * factor))
        setattr(self, stat, after)
        self.update_stage()
        return after - before

    def train(self, stat: str) -> int:
        """능력치를 훈련한다: 성장 + 스트레스 증가. 실제 증가량 반환."""
        gained = self.grow(stat, config.TRAIN_AMOUNT)
        self.stress = _clamp(self.stress + config.STRESS_PER_TRAIN)
        return gained

    def apply_effects(self, effects: dict) -> None:
        """효과 dict를 적용한다(아이템·돌봄 공용). 능력치는 자동으로 범위 제한."""
        for key, delta in effects.items():
            if key == "currency":
                self.currency = max(0, self.currency + delta)
            elif key in CLAMPED_FIELDS:
                setattr(self, key, _clamp(getattr(self, key) + delta))
            else:
                raise ValueError(f"적용할 수 없는 효과: {key}")
        self.update_stage()

    def stat_total(self) -> int:
        """핵심 능력치 합 (진화·엔딩 판정 기준)."""
        return sum(getattr(self, s) for s in CORE_STATS)

    def update_stage(self) -> int:
        """누적 능력치에 따라 성장 단계를 갱신하고 단계 값을 반환한다."""
        total = self.stat_total()
        stage = 0
        for i, threshold in enumerate(config.STAGE_THRESHOLDS):
            if total >= threshold:
                stage = i
        self.stage = stage
        return stage

    # ── XP / 레벨 (전체 진행도) ──────────────────────────
    def level(self) -> int:
        """누적 XP로부터 파생된 현재 레벨(1~)."""
        return progression.level_for_xp(self.xp)

    def level_title(self) -> str:
        """현재 레벨의 마일스톤 타이틀(예: '어린이')."""
        return progression.title_for_level(self.level())

    def xp_progress(self) -> tuple[int, int, float]:
        """현재 레벨 구간의 (채운 XP, 필요 XP, 진행비율). HUD 진행 바에 쓴다."""
        return progression.progress(self.xp)

    def add_xp(self, amount: int) -> tuple[int, int]:
        """XP를 더하고 (이전 레벨, 새 레벨)을 반환한다. 레벨업 감지용."""
        before = self.level()
        self.xp = max(0, self.xp + int(amount))
        return before, self.level()

    # ── 직렬화 ──────────────────────────────────────────
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        """알 수 없는 키는 무시하고 캐릭터를 복원한다."""
        valid = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in valid})
