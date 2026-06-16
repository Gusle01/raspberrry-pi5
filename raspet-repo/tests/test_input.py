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


class _FakeJoystick:
    available = True

    def __init__(self):
        self._dir = "center"
        self._pressed = False

    def direction(self):
        return self._dir

    def pressed(self):
        return self._pressed


def test_joystick_sw_press_is_confirm_edge():
    fj = _FakeJoystick()
    ctx = GameContext(hardware={"joystick": fj}, headless=True)
    # 안 눌림 → 확인 없음
    assert "a" not in ctx.poll()
    # 스위치가 0이 되어 눌림 → 확인(a) 1회
    fj._pressed = True
    assert "a" in ctx.poll()
    # 계속 눌려 있어도 엣지는 1회뿐(연타 방지)
    assert "a" not in ctx.poll()
    # 뗐다가 다시 누르면 또 확인
    fj._pressed = False; ctx.poll()
    fj._pressed = True
    assert "a" in ctx.poll()


def test_joystick_sw_confirm_even_when_tilted():
    # center가 아니어도(스틱을 민 채로) 눌리면 확인이 된다.
    fj = _FakeJoystick()
    fj._dir = "right"
    ctx = GameContext(hardware={"joystick": fj}, headless=True)
    ctx.poll()                       # 'right' 엣지 소비
    fj._pressed = True
    assert "a" in ctx.poll()


def test_adc_button_median_debounce():
    # 풀업 없는 CH0: 5표본 중앙값으로 순간 튐을 걸러 눌림/뗌을 판정한다.
    from raspet.hardware.joystick import Joystick

    class _FakeADC:
        def __init__(self, seq):
            self._seq, self._i = list(seq), 0

        @property
        def value(self):
            v = self._seq[self._i % len(self._seq)]
            self._i += 1
            return v

    j = Joystick.__new__(Joystick)        # __init__(하드웨어) 우회
    j._button = None
    # 대부분 0(누름) + 스파이크 1개 → 중앙값 0 → 눌림
    j._adc_button = _FakeADC([0.0, 0.0, 0.5, 0.0, 0.0])
    assert j.pressed() is True
    # 대부분 높음(뗌) + 순간 0 하나 → 중앙값 높음 → 안 눌림(헛인식 방지)
    j._adc_button = _FakeADC([0.40, 0.45, 0.0, 0.42, 0.40])
    assert j.pressed() is False


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


# ── 4번째 LED(파랑) + 온도/색깔찾기 색 표시 ──────────────
class _FakeEnv:
    def __init__(self, temp):
        self._t = temp

    def read(self):
        from raspet.hardware.environment import EnvReading
        return EnvReading(temperature_c=self._t)


def _ctx_temp(temp, leds=None):
    hw = {"env": _FakeEnv(temp)}
    if leds is not None:
        hw["leds"] = leds
    return GameContext(hardware=hw, headless=True)


def test_led_config_has_four_colors():
    assert len(config.PIN_LEDS) == len(config.LED_COLORS) == 4
    assert "blue" in config.LED_COLORS
    # 색깔 찾기 타깃이 모두 실제 LED 색으로 매핑되는지
    for name, *_ in config.COLOR_HUNT_TARGETS:
        assert config.COLOR_HUNT_LED.get(name) in config.LED_COLORS


def test_temp_led_color_thresholds():
    assert _ctx_temp(30).temp_led_color() == config.TEMP_LED_HOT     # 더움
    assert _ctx_temp(20).temp_led_color() == config.TEMP_LED_OK      # 적당
    assert _ctx_temp(5).temp_led_color() == config.TEMP_LED_COLD     # 추움
    assert _ctx_temp(None).temp_led_color() is None                  # 센서 없음


def test_update_temp_led_lights_only_that_color():
    fl = _FakeLeds()
    _ctx_temp(30, leds=fl).update_temp_led()                # 더움 → 빨강만
    red_i = config.LED_COLORS.index("red")
    assert fl.state.get(red_i) is True
    assert all(v is False for k, v in fl.state.items() if k != red_i)


def test_update_temp_led_off_without_sensor():
    fl = _FakeLeds()
    _ctx_temp(None, leds=fl).update_temp_led()
    assert all(v is False for v in fl.state.values())


def test_set_color_led_lights_only_named():
    fl = _FakeLeds()
    ctx = GameContext(hardware={"leds": fl}, headless=True)
    ctx.set_color_led("blue")
    blue_i = config.LED_COLORS.index("blue")
    assert fl.state.get(blue_i) is True
    assert all(v is False for k, v in fl.state.items() if k != blue_i)
    ctx.set_color_led(None)                                 # 전부 끔
    assert all(v is False for v in fl.state.values())
