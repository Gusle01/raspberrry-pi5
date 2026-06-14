"""버튼 입력 매핑(상황별) · 확인/뒤로 표시 LED 테스트."""
from raspet.core.context import GameContext
from raspet import config


class _FakeButtons:
    available = True

    def __init__(self):
        self._edges = set()

    def queue(self, *idx):
        self._edges = set(idx)

    def pressed_edges(self):
        e, self._edges = self._edges, set()
        return e


class _FakeLeds:
    available = True

    def __init__(self):
        self.state = {}

    def set(self, i, on):
        self.state[i] = bool(on)

    def all_off(self):
        for k in list(self.state):
            self.state[k] = False


# ctx.quit()은 pygame.quit()을 호출해 다른 테스트에 영향을 주므로 부르지 않는다.
def test_buttons_menu_mode_confirm_and_back():
    fb = _FakeButtons()
    ctx = GameContext(hardware={"buttons": fb}, headless=True)
    # 기본(메뉴) 매핑: 초록(0)=확인, 빨강(1)=뒤로, 노랑(2)=아래
    fb.queue(0); assert "a" in ctx.poll()
    fb.queue(1); assert "b" in ctx.poll()
    fb.queue(2); assert "down" in ctx.poll()


def test_buttons_game_mode_are_holes():
    fb = _FakeButtons()
    ctx = GameContext(hardware={"buttons": fb}, headless=True)
    ctx.set_button_actions(config.BUTTON_GAME_ACTIONS)   # 두더지 모드
    fb.queue(0); assert "left" in ctx.poll()
    fb.queue(1); assert "down" in ctx.poll()
    fb.queue(2); assert "right" in ctx.poll()
    # 두더지 모드에선 확인/뒤로가 나오지 않는다
    fb.queue(0); assert "a" not in ctx.poll()
    # 메뉴 모드로 복귀
    ctx.use_menu_buttons()
    fb.queue(1); assert "b" in ctx.poll()


def test_indicator_leds_light_confirm_and_back():
    fl = _FakeLeds()
    ctx = GameContext(hardware={"leds": fl}, headless=True)
    ctx.update_indicator_leds()
    assert fl.state.get(0) is True     # 초록=확인 → 켜짐
    assert fl.state.get(1) is True     # 빨강=뒤로 → 켜짐
    assert fl.state.get(2) is False    # 노랑=이동 → 꺼짐
