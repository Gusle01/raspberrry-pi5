"""상점 구매 로직 테스트."""
from raspet.character.character import Character
from raspet.shop.shop import Shop


def test_buy_success_deducts_and_applies_effect():
    shop = Shop()
    book = shop.get("book")
    ch = Character(currency=book.price, intellect=10)
    assert shop.buy(ch, book) is True
    assert ch.currency == 0
    assert ch.intellect == 10 + book.effect["intellect"]
    assert "book" in ch.inventory          # 기능 아이템은 보유됨


def test_buy_insufficient_funds():
    shop = Shop()
    cape = shop.get("cape")
    ch = Character(currency=cape.price - 1)
    assert shop.buy(ch, cape) is False
    assert ch.currency == cape.price - 1
    assert "cape" not in ch.inventory


def test_consumable_not_added_to_inventory():
    shop = Shop()
    snack = shop.get("snack")
    ch = Character(currency=snack.price, fullness=0)
    assert shop.buy(ch, snack) is True
    assert "snack" not in ch.inventory     # 소비 아이템은 즉시 소모
    assert ch.fullness == snack.effect["fullness"]


def test_catalog_loaded():
    shop = Shop()
    assert len(shop.catalog) >= 1
    assert shop.get("hat") is not None
