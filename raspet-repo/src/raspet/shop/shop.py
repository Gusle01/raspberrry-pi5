"""상점 및 재화 시스템.

미니게임으로 얻은 재화로 코스튬·소비 아이템·기능 아이템을 구매한다.
(계획서 4.3)
"""
from dataclasses import dataclass


@dataclass
class Item:
    item_id: str
    name: str
    price: int
    category: str   # "costume" | "consumable" | "function"


# 상점 품목 예시 (계획서 4.3 표)
CATALOG = [
    # TODO: 모자/옷/배경, 먹이/간식/장난감, 능력치 초기화권, 성장 부스터 등 정의
]


class Shop:
    """구매 처리 및 효과 적용."""

    def buy(self, character, item: Item) -> bool:
        """재화가 충분하면 구매하고 효과를 적용한다."""
        # TODO: 재화 차감, 인벤토리 추가/효과 적용
        raise NotImplementedError
