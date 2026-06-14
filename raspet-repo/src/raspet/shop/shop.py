"""상점 및 재화 시스템.

미니게임으로 얻은 재화로 코스튬·소비 아이템·기능 아이템을 구매한다.
품목/가격/효과 등 밸런스 값은 config.SHOP_ITEMS 에서 가져온다. (계획서 4.3)
"""
from dataclasses import dataclass

from .. import config


@dataclass(frozen=True)
class Item:
    item_id: str
    name: str
    price: int
    category: str        # "costume" | "consumable" | "function"
    effect: dict         # 구매 시 캐릭터에 적용할 능력치 변화


def load_catalog() -> list[Item]:
    """config.SHOP_ITEMS 정의로부터 Item 목록을 만든다."""
    return [Item(item_id=spec["id"], name=spec["name"], price=spec["price"],
                 category=spec["category"], effect=dict(spec.get("effect", {})))
            for spec in config.SHOP_ITEMS]


# 즉시 효과가 적용되고 사라지는(인벤토리에 남지 않는) 카테고리
_CONSUMED_ON_BUY = {"consumable"}


class Shop:
    """구매 처리 및 효과 적용."""

    def __init__(self) -> None:
        self.catalog = load_catalog()
        self._by_id = {item.item_id: item for item in self.catalog}

    def get(self, item_id: str) -> Item | None:
        return self._by_id.get(item_id)

    def can_afford(self, character, item: Item) -> bool:
        return character.currency >= item.price

    def buy(self, character, item: Item) -> bool:
        """재화가 충분하면 구매하고 효과를 적용한다. 성공 여부 반환."""
        if not self.can_afford(character, item):
            return False
        character.currency -= item.price
        if item.effect:
            character.apply_effects(item.effect)
        # 소비 아이템은 즉시 소모, 그 외(코스튬·기능)는 보유 목록에 남긴다.
        if item.category not in _CONSUMED_ON_BUY:
            character.inventory.append(item.item_id)
        return True
