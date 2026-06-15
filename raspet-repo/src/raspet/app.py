"""애플리케이션 부트스트랩.

하드웨어/디스플레이를 초기화하고 저장 데이터를 불러온 뒤 게임 루프를 시작한다.
하드웨어가 없으면 자동으로 더미로 폴백하므로 PC에서도 그대로 실행된다.
환경변수:
  RASPET_DUMMY=1     실제 장치를 잡지 않고 더미로 동작
  RASPET_HEADLESS=1  창/OLED 없이 실행(자동 테스트용)
"""
from .core.context import GameContext
from .core.game_loop import GameLoop
from .hardware.display import create_display
from .hardware.joystick import create_joystick
from .hardware.ultrasonic import create_ultrasonic
from .hardware.buzzer import create_buzzer
from .hardware.leds import create_leds, DummyLeds
from .hardware.buttons import create_buttons, DummyButtons
from .hardware.keypad import create_keypad
from .hardware.segment_display import create_segment_display
from .hardware.environment import create_environment
from .vision.camera import create_camera
from .vision.hand import create_hand_recognizer
from . import config
from .storage import save


def build_hardware() -> dict:
    """연결된 장치를 잡거나 더미로 폴백한 하드웨어 묶음을 만든다."""
    # 키패드를 쓰면 3버튼과 핀(16·20·21)을 공유하므로 별도 버튼 장치는 더미로 둔다.
    buttons = DummyButtons() if config.KEYPAD_ENABLED else create_buttons()
    # 7세그먼트를 쓰면 LED 핀(5·6·13)을 자릿수 공통선으로 재사용하므로 LED는 더미로 둔다.
    leds = DummyLeds() if config.SEG_ENABLED else create_leds()
    return {
        "display": create_display(),
        "joystick": create_joystick(),
        "ultrasonic": create_ultrasonic(),
        "buzzer": create_buzzer(),
        "leds": leds,
        "buttons": buttons,
        "keypad": create_keypad(),
        "env": create_environment(),
        "camera": create_camera(),
        "hand": create_hand_recognizer(),
        "segment": create_segment_display(),
    }


def main() -> None:
    """RasPet을 실행한다."""
    hardware = build_hardware()
    ctx = GameContext(hardware=hardware)
    character, last_saved_ts = save.load_character()
    game = GameLoop(ctx, character, last_saved_ts)
    try:
        game.run()
    finally:
        ctx.quit()


if __name__ == "__main__":
    main()
