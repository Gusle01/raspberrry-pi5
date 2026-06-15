"""4×4 매트릭스 키패드 — 엣지 검출·라벨, 그리고 키패드 두더지 잡기 셀 매핑."""
from raspet.hardware.keypad import Keypad, DummyKeypad, create_keypad
from raspet.minigames.whack_a_mole import WhackAMole, WhackEngine
from raspet import config


class _FakeKeypad(Keypad):
    """scan()을 직접 제어하는 테스트용 키패드(엣지 로직은 베이스 클래스 그대로 사용)."""

    def __init__(self):
        self._rows = [object()] * 4      # 비어있지 않게 두어 available=True
        self._cols = [object()] * 4
        self.layout = config.KEYPAD_LAYOUT
        self._prev = set()
        self.held = set()                # 지금 눌린 셀(테스트가 바꿈)

    @property
    def available(self) -> bool:
        return True

    def scan(self) -> set:
        return set(self.held)


# ── 드라이버 ─────────────────────────────────────────────
def test_dummy_keypad_is_empty():
    kp = DummyKeypad()
    assert kp.available is False
    assert kp.scan() == set()
    assert kp.pressed_edges() == set()


def test_create_keypad_dummy_under_flag():
    # 테스트 환경(RASPET_DUMMY=1)에서는 항상 더미.
    assert isinstance(create_keypad(), DummyKeypad)


def test_key_label_from_layout():
    kp = _FakeKeypad()
    assert kp.key_label(0, 0) == "1"
    assert kp.key_label(0, 3) == "A"
    assert kp.key_label(3, 2) == "#"
    assert kp.key_label(9, 9) == ""        # 범위 밖은 빈 문자열


def test_menu_actions_match_designated_switches():
    # 사용자 지정 물리 스위치(S1~S16, 행 우선) → 메뉴 행동이 올바로 매핑되는지.
    s = lambda n: ((n - 1) // 4, (n - 1) % 4)      # S번호 → (row, col)
    expected = {16: "right", 15: "down", 14: "left", 11: "up", 4: "a", 1: "b"}
    for num, action in expected.items():
        r, c = s(num)
        label = config.KEYPAD_LAYOUT[r][c]
        assert config.KEYPAD_MENU_ACTIONS.get(label) == action
    assert config.KEYPAD_BACK_KEY == config.KEYPAD_LAYOUT[0][0]   # S1 = 뒤로


def test_pressed_edges_only_new_presses():
    kp = _FakeKeypad()
    kp.held = {(0, 0)}
    assert kp.pressed_edges() == {(0, 0)}      # 새로 눌림
    assert kp.pressed_edges() == set()         # 계속 눌려 있어도 엣지는 1회뿐
    kp.held = {(0, 0), (1, 1)}
    assert kp.pressed_edges() == {(1, 1)}      # 추가된 것만
    kp.held = set()
    assert kp.pressed_edges() == set()         # 뗌


# ── 키패드 두더지 잡기: 셀(row,col) → 구멍 인덱스 ────────
def test_grid_keypad_hits_correct_cell():
    g = WhackAMole(ctx=None)
    g._grid = (4, 4)
    g.engine = WhackEngine(holes=16)
    g._keypad = _FakeKeypad()
    # (1,2) → idx = 1*4+2 = 6. 그 자리에 두더지를 놓고 누른다.
    g.engine.moles[6] = {"kind": "mole", "age": 0.0, "ttl": 1.0}
    g._keypad.held = {(1, 2)}
    aborted = g._read_keypad()
    assert aborted is False
    assert g.engine.hits == 1 and 6 not in g.engine.moles


def test_grid_keypad_back_key_aborts():
    g = WhackAMole(ctx=None)
    g._grid = (4, 4)
    g.engine = WhackEngine(holes=16)
    g._keypad = _FakeKeypad()
    # 뒤로 키(config.KEYPAD_BACK_KEY, S1='1')의 위치를 찾아 누른다.
    pos = next((r, c) for r in range(4) for c in range(4)
               if config.KEYPAD_LAYOUT[r][c] == config.KEYPAD_BACK_KEY)
    g._keypad.held = {pos}
    assert g._read_keypad() is True            # 중단 신호
