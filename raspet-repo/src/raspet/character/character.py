"""캐릭터 데이터 모델과 능력치(스탯) 시스템."""
from dataclasses import dataclass, field


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
    stage: int = 0          # 성장 단계(진화)

    def grow(self, stat: str, amount: int) -> None:
        """능력치를 올린다 (상한 적용)."""
        # TODO: 스트레스가 높으면 성장 효율 감소 적용
        raise NotImplementedError
