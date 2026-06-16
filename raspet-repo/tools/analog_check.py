"""아날로그(MCP3008·SPI) 입력 진단 — 조이스틱 + 조도(LDR).

게임이 실제로 쓰는 코드 경로(gpiozero.MCP3008)로 읽어, 정규화 값과 게임의
해석(조이스틱 direction / 밤·낮 판정)을 실시간으로 보여준다.
spidev 단독 테스트는 '원시값이 변한다'까지만 확인되지만, 게임은 그 값을
데드존·극성(LIGHT_INVERT)·임계값으로 해석하므로 여기서 그 해석까지 본다.

실행:  ../.venv/bin/python tools/analog_check.py     (raspet-repo 안에서)

확인 포인트
  • 조이스틱: 끝까지 밀면 x/y가 ±1 근처까지 가는가? dir이 center를 벗어나는가?
            (안 벗어나면 JOYSTICK_DEADZONE이 너무 큼)
  • 조이스틱 버튼: 누르면 pressed=True 가 되는가?
            (안 되면 SW가 GPIO%(btn)s 가 아니라 다른 곳(예: ADC)에 배선된 것)
  • 조도(LDR): 손전등을 비추면 light가 1.0 쪽으로, 가리면 0.0 쪽으로 가는가?
            거꾸로면 config.LIGHT_INVERT 를 True 로 바꾸면 됨.
            'DAY/NIGHT' 판정이 실제 밝기와 맞는지도 함께 본다.
"""
import sys, time
sys.path.insert(0, "src")

from raspet import config
from raspet.hardware.joystick import create_joystick, _GPIO_AVAILABLE
from raspet.hardware.environment import Environment

print(__doc__ % {"btn": config.PIN_JOYSTICK_BUTTON})
print(f"_GPIO_AVAILABLE={_GPIO_AVAILABLE} USE_DUMMY={config.USE_DUMMY_HARDWARE}")
print(f"채널: X={config.ADC_CHANNEL_X} Y={config.ADC_CHANNEL_Y} "
      f"LIGHT={config.ADC_CHANNEL_LIGHT} 버튼GPIO={config.PIN_JOYSTICK_BUTTON}")
print(f"데드존={config.JOYSTICK_DEADZONE} LIGHT_INVERT={config.LIGHT_INVERT} "
      f"밤판정임계={config.LIGHT_DARK_BELOW}")

joy = create_joystick()
env = Environment()
print(f"\n조이스틱: {type(joy).__name__} available={joy.available} | "
      f"조도 available={env.light_available}\n")
if not joy.available and not env.light_available:
    print("→ 둘 다 더미 폴백! gpiozero/SPI 문제.")
    raise SystemExit

print("조이스틱을 밀고/누르고, LDR을 비추거나 가려보세요. Ctrl+C로 종료.\n")
try:
    while True:
        line = ""
        if joy.available:
            x, y = joy.read()
            line += f"x={x:+.2f} y={y:+.2f} dir={joy.direction():>6} press={joy.pressed()!s:5} "
        if env.light_available:
            lv = env.light()
            night = lv is not None and lv <= config.LIGHT_DARK_BELOW
            line += f"| light={lv:.3f} -> {'NIGHT(잠)' if night else 'DAY(깸)'}"
        print(line)
        time.sleep(0.2)
except KeyboardInterrupt:
    print("\n종료")
