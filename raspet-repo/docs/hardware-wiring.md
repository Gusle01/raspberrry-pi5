# 🔌 RasPet 하드웨어 배선 가이드

라즈베리파이 5 기준. 핀 번호는 모두 **BCM(GPIO) 번호**이며, 값은 [`src/raspet/config.py`](../src/raspet/config.py)에서 가져온 것입니다. 배선을 바꾸면 **코드가 아니라 `config.py`만** 수정하세요.

> 🗺️ **40핀 헤더에 모듈을 그림으로 매핑한 다이어그램**과 부품 목록(BOM)·Fritzing 부품 목록은 [`wiring-diagram.md`](wiring-diagram.md)를 참고하세요.

> ⚠️ Pi 5는 `RPi.GPIO`가 동작하지 않습니다. 본 프로젝트는 `gpiozero` + `lgpio` 백엔드를 사용합니다.

---

## 📋 핀 배정 요약

| 장치 | 신호 | 연결 | config 상수 |
|---|---|---|---|
| OLED (SSD1306, I2C) | SDA | GPIO2 (핀 3) | — (I2C 고정) |
| | SCL | GPIO3 (핀 5) | — |
| | 주소 | `0x3C` | `display.py` |
| MCP3008 (SPI0) | CLK | GPIO11 (핀 23) | — (SPI 고정) |
| | MISO (DOUT) | GPIO9 (핀 21) | — |
| | MOSI (DIN) | GPIO10 (핀 19) | — |
| | CS (CE0) | GPIO8 (핀 24) | — |
| 조이스틱 | VRx → MCP3008 CH0 | ADC 채널 0 | `ADC_CHANNEL_X = 0` |
| | VRy → MCP3008 CH1 | ADC 채널 1 | `ADC_CHANNEL_Y = 1` |
| | SW (버튼) | GPIO25 (핀 22) | `PIN_JOYSTICK_BUTTON = 25` |
| 초음파 HC-SR04 | TRIG | GPIO23 (핀 16) | `PIN_ULTRASONIC_TRIG = 23` |
| | ECHO | GPIO24 (핀 18) ※분압 | `PIN_ULTRASONIC_ECHO = 24` |
| 부저(피에조) | 신호 | GPIO18 (핀 12, PWM) | `PIN_BUZZER = 18` |
| 두더지 LED ×3 | 신호 | GPIO5·6·13 (핀 29·31·33) → 220~330Ω → LED → GND | `PIN_LEDS = [5, 6, 13]` |
| 두더지 버튼 ×3 | 신호 | GPIO16·20·21 (핀 36·38·40) → 버튼 → GND | `PIN_BUTTONS = [16, 20, 21]` |
| 카메라 | CSI | 전용 CSI 커넥터 | — |

전원: 각 모듈 VCC는 3.3V 또는 5V(모듈 사양 확인), GND는 공통 접지.

---

## ⚡ 주의사항 (중요)

### 1. HC-SR04 ECHO는 반드시 분압
HC-SR04의 ECHO 출력은 **5V**라서 Pi의 3.3V GPIO에 직접 연결하면 핀이 손상될 수 있습니다.
저항 분압(예: R1 = 1kΩ, R2 = 2kΩ)으로 약 3.3V로 낮춰 연결하세요.

```
ECHO ──[ 1kΩ ]──┬── GPIO24
                │
              [ 2kΩ ]
                │
               GND
```
TRIG는 입력이므로 3.3V 신호로 충분합니다. VCC는 5V를 사용하세요.

### 2. MCP3008 (아날로그 조이스틱)
Pi에는 ADC가 없어 SPI ADC가 필요합니다. MCP3008 VDD/VREF=3.3V, AGND/DGND=GND.
조이스틱 VRx/VRy를 CH0/CH1에 연결합니다. 축 방향이 반대로 읽히면
`hardware/joystick.py`의 정규화/`direction()` 부호를 배선에 맞게 조정하세요.

### 3. OLED는 I2C, MCP3008은 SPI
서로 다른 버스라 충돌하지 않습니다. 디스플레이를 SPI 모델(SSD1351/ST7789)로
바꾸는 경우 `hardware/display.py`의 드라이버/인터페이스를 교체하세요.

### 4. LED·버튼 + 조작 매핑
- **LED 3개:** 각 GPIO(5·6·13) → **220~330Ω 저항** → LED(애노드), LED(캐소드) → GND.
- **버튼 3개:** 각 GPIO(16·20·21) → 버튼 → GND. 코드가 **내부 풀업**(`pull_up=True`)을
  쓰므로 외부 저항이 필요 없습니다(평소 HIGH, 누르면 LOW).
- LED와 버튼은 같은 인덱스(0·1·2)끼리 한 쌍입니다. 각 자리에 꽂은 LED 색은
  `config.LED_COLORS`에 적어 배선에 맞추세요(기본 `["green","red","yellow"]`).

**버튼은 상황에 따라 역할이 바뀝니다.**
- **평소(메뉴 등):** `config.BUTTON_MENU_ACTIONS` — **초록 LED 버튼 = 확인('a')**,
  **빨강 LED 버튼 = 뒤로('b')**, 노랑 = 메뉴 아래로. 확인/뒤로 버튼의 LED는 켜져서
  어떤 버튼인지 표시됩니다(`BUTTON_LED_INDICATORS`).
- **두더지 잡기 중:** `config.BUTTON_GAME_ACTIONS` — 3버튼 모두 **구멍(왼·가운데·오른쪽)**
  전용이 되고 확인/뒤로는 동작하지 않습니다. 끝나면 자동으로 평소 모드로 복귀합니다.
- **조이스틱:** 메뉴 이동(상하좌우) + 누름 = 확인('a'). PC에서는 방향키·Enter/Esc로 동일.

> 색 배치를 바꾸려면 `config.LED_COLORS`만 실제 배선에 맞게 고치면 확인/뒤로/표시 LED가
> 모두 따라 바뀝니다.

```
GPIO5 ──[ 220Ω ]──▷|── GND      (LED 0, 가운데/오른쪽도 동일)
GPIO16 ─────────[버튼]───── GND   (버튼 0, 내부 풀업)
```

---

## 🛠️ 인터페이스 활성화

```bash
sudo raspi-config        # Interface Options → I2C, SPI 활성화
sudo reboot

# 연결 확인
i2cdetect -y 1           # OLED가 0x3C로 보이는지
ls /dev/spidev*          # spidev0.0 존재 확인
```

picamera2는 보통 OS에 포함되어 있습니다: `sudo apt install -y python3-picamera2`

---

## ✅ 개별 동작 점검 (로드맵 2단계)

장치를 하나씩 붙여가며 확인하세요. 코드는 장치가 없으면 더미로 폴백하므로,
아래처럼 팩토리의 `available` 플래그로 인식 여부를 빠르게 확인할 수 있습니다.

```bash
cd raspet-repo
python3 - <<'PY'
import sys; sys.path.insert(0, "src")
from raspet.hardware.display import create_display
from raspet.hardware.joystick import create_joystick
from raspet.hardware.ultrasonic import create_ultrasonic
from raspet.hardware.leds import create_leds
from raspet.hardware.buttons import create_buttons
print("OLED   :", create_display().available)
print("조이스틱:", create_joystick().available)
print("초음파  :", create_ultrasonic().available)
print("LED    :", create_leds().available)
print("버튼    :", create_buttons().available)
PY
```

`available`이 `False`로 나오면 배선·인터페이스 활성화·라이브러리 설치를 점검하세요.
값이 이상하게 읽히면 `config.py`의 핀 번호부터 확인합니다.
