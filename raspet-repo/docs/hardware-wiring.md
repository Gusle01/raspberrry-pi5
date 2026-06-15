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
| 조도센서(LDR) | 분압 출력 → MCP3008 CH2 | ADC 채널 2 | `ADC_CHANNEL_LIGHT = 2` |
| BMP180 (온도·기압, I2C) | SDA/SCL | GPIO2·3 (OLED와 공유) | `BMP180_I2C_ADDR = 0x77` |
| 초음파 HC-SR04 | TRIG | GPIO23 (핀 16) | `PIN_ULTRASONIC_TRIG = 23` |
| | ECHO | GPIO24 (핀 18) ※분압 | `PIN_ULTRASONIC_ECHO = 24` |
| 부저(피에조) | 신호 | GPIO18 (핀 12, PWM) | `PIN_BUZZER = 18` |
| LED ×4 (초록·빨강·노랑·파랑) | 신호 | GPIO5·6·13·19 (핀 29·31·33·35) → 220~330Ω → LED → GND | `PIN_LEDS = [5, 6, 13, 19]` |
| 두더지 버튼 ×3 | 신호 | GPIO16·20·21 (핀 36·38·40) → 버튼 → GND | `PIN_BUTTONS = [16, 20, 21]` |
| 4×4 키패드 | 행(출력) | GPIO26·17·27·22 (핀 37·11·13·15) | `PIN_KEYPAD_ROWS` |
| | 열(입력·풀업) | GPIO12·16·20·21 (핀 32·36·38·40) | `PIN_KEYPAD_COLS` |
| 7세그 4자리 (74HC595) | DS(데이터) | GPIO14 (핀 8) | `PIN_7SEG_DATA = 14` |
| | SHCP(시프트클럭) | GPIO15 (핀 10) | `PIN_7SEG_CLOCK = 15` |
| | STCP(래치) | GPIO19 (핀 35) | `PIN_7SEG_LATCH = 19` |
| | 자릿수 공통 ×4 ※트랜지스터 | GPIO5·6·13·4 (핀 29·31·33·7) | `PIN_7SEG_DIGITS = [5,6,13,4]` |
| 카메라 | CSI | 전용 CSI 커넥터 | — |

> ⚠️ **7세그(HSN-3643AS)는 LED 4핀(5·6·13·19)을 세그먼트/래치로 재사용**한다. 둘은 같은
> 핀이라 동시 사용 불가 — 기본(`RASPET_7SEG=0`)은 LED 4개 모드, `RASPET_7SEG=1`이면 7세그 모드로 자동
> 폴백한다. 또 자릿수 GPIO4는 **1-Wire 오버레이를 꺼야** 쓸 수 있다(아래 3-4 참고).

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

### 3-1. 조도센서(LDR) — MCP3008 CH2 분압
LDR은 빛의 세기에 따라 저항이 변합니다. 고정저항(10kΩ 권장)과 직렬로 분압해
**가운데 지점**을 MCP3008 CH2에 연결합니다.

```
3.3V ──[ LDR ]──┬── MCP3008 CH2   (밝을수록 값 ↑)
                │
             [ 10kΩ ]
                │
               GND
```
- 위 배선은 **밝을수록 ADC 값이 커집니다.** LDR과 저항 위치를 바꾸면 반대로 읽히는데,
  그 경우 `config.LIGHT_INVERT = True`로 두면 코드가 값을 뒤집어 줍니다.
- 어두움/밝음 임계값은 `config.LIGHT_DARK_BELOW`(이하=밤·잠) /
  `config.LIGHT_LIGHT_ABOVE`(이상=낮·기상)로 조정합니다. 경계 깜빡임을 막는 히스테리시스.

### 3-2. BMP180(온도·기압) — I2C 공유
OLED와 **같은 I2C 버스**(SDA=GPIO2, SCL=GPIO3)에 병렬로 연결합니다. 주소는 `0x77`이라
OLED(`0x3C`)와 겹치지 않습니다. VCC는 모듈 사양에 맞춰 3.3V 권장.
- 연결 확인: `i2cdetect -y 1` → `0x3c`(OLED)와 `0x77`(BMP180)이 함께 보여야 합니다.
- ⚠️ **BMP180은 습도를 측정하지 못합니다(온도+기압만).** 습도까지 필요하면 핀 호환인
  **BME280**으로 교체하고 `hardware/environment.py`의 `read()`에서 `humidity`를 채우면 됩니다.

### 3-3. 4×4 매트릭스 키패드
행 4개(GPIO26·17·27·22)는 출력, 열 4개(GPIO12·16·20·21)는 입력(내부 풀업)입니다.
> ⚠️ GPIO4는 1-Wire(`dtoverlay=w1-gpio`)가 점유하므로 행1은 **GPIO26(물리핀 37)** 을 씁니다.
> (1-Wire를 끄면 GPIO4로 되돌릴 수 있음.)
스캔: 한 행만 LOW로 내리고 각 열을 읽어, LOW인 열이 그 행에서 눌린 키입니다.
- ⚠️ **키패드는 기존 3버튼과 핀(16·20·21)을 공유합니다.** `KEYPAD_ENABLED=True`(기본)이면
  3버튼 장치를 만들지 않고 키패드가 그 자리를 대신합니다(둘을 동시에 달지 마세요).
  키패드 없이 3버튼만 쓰려면 `RASPET_KEYPAD=0`으로 실행합니다.
- 키 배치는 `config.KEYPAD_LAYOUT`, 메뉴 동작 매핑은 `config.KEYPAD_MENU_ACTIONS`에서 바꿉니다.
  현재 물리 스위치 기준 매핑: **S11=위, S14=왼쪽, S15=아래, S16=오른쪽, S4=확인, S1=뒤로**.
  두더지 잡기는 OLED 4×4 격자에 각 칸의 키 라벨을 표시하므로 어느 키를 누를지 바로 보입니다.

### 3-4. 4자리 7세그먼트 (HSN-3643AS + 74HC595)
드라이버 칩이 없는 '맨' 4자리 공통캐소드 모듈이라, **세그먼트는 74HC595 1개**로, **자릿수
공통선 4개는 GPIO**로 멀티플렉싱한다(한 번에 한 자리만 켜고 빠르게 돌림 — 백그라운드 스레드가 전담).

- **74HC595 → 세그먼트:** 595의 Q0~Q7 출력 → 각 **220~330Ω** → 세그먼트 a~g·dp 핀.
  Pi는 DS(14)·SHCP(15)·STCP(19) 3선만 연결. 595의 OE→GND, MR(MCLR)→3.3V, VCC/GND 연결.
  595 출력↔세그먼트 순서가 다르면 코드는 그대로 두고 `config.SEG_ORDER`만 바꾼다.
- **자릿수 공통선(4):** GPIO5·6·13·4 → **각각 NPN 트랜지스터**(예: 2N3904/2N2222, 베이스에 1kΩ)
  → 디스플레이 자릿수 공통(캐소드) → GND.
  > ⚠️ **GPIO에 자릿수 공통을 직결하지 말 것.** 한 자리의 세그먼트 8개 전류가 공통선 하나로
  > 합쳐져 흐르므로(최대 수십 mA) GPIO 허용치(~16mA)를 넘긴다. 트랜지스터로 받아 GND로 흘린다.
  > (ULN2003/2803 달링턴 어레이 하나로 4채널을 한 번에 받아도 됨.)
- **GPIO4 쓰려면 1-Wire 끄기:** `/boot/firmware/config.txt`에서 `dtoverlay=w1-gpio` 줄을 지우고
  재부팅한다(BMP180는 I2C라 1-Wire는 더 이상 필요 없음).
- **표시 내용:** 평소 화면=주변 온도(`25°C`), 시간제한 미니게임(색깔찾기·가위바위보·두더지)=남은 시간.
- **기본은 꺼짐(LED 우선):** 기본값 `RASPET_7SEG=0`은 GPIO5·6·13·19를 **LED 4개**로 쓴다.
  7세그를 쓰려면 트랜지스터를 단 뒤 `RASPET_7SEG=1`로 실행한다(LED는 그때 자동으로 더미가 됨).

### 4. LED·버튼 + 조작 매핑
- **LED 4개(초록·빨강·노랑·파랑):** 각 GPIO(5·6·13·19) → **220~330Ω 저항** → LED(애노드), LED(캐소드) → GND.
  색은 `config.LED_COLORS`(기본 `["green","red","yellow","blue"]`)에 배선 순서대로 적는다.
- **버튼 3개:** 각 GPIO(16·20·21) → 버튼 → GND. 코드가 **내부 풀업**(`pull_up=True`)을
  쓰므로 외부 저항이 필요 없습니다(평소 HIGH, 누르면 LOW). (LED 0·1·2와 버튼이 한 쌍, 파랑(3)은 버튼 짝 없음.)

**LED 4개의 쓰임:**
- **메인 화면 = 온도 색:** 더움(≥`TEMP_HOT_ABOVE_C`)=🔴빨강, 적당=🟢초록, 추움(≤`TEMP_COLD_BELOW_C`)=🔵파랑.
  얼굴 표정(땀/눈송이)과 짝을 이룬다. 센서 없으면 소등. (`config.TEMP_LED_HOT/OK/COLD`)
- **색깔 찾기 = 색 힌트:** 찾을 색의 LED가 켜진다 — 흑백 OLED가 못 보여주는 실제 색을 알려줌(`config.COLOR_HUNT_LED`).
- **두더지 잡기 = 표시등:** 초록=콤보 중, 빨강=함정 주의, 노랑=두더지 등장.
- ⚠️ **7세그먼트(3-4)를 켜면(`RASPET_7SEG=1`) 이 LED 핀(5·6·13·19)이 7세그로 넘어가** LED는
  더미가 됩니다. 기본값은 꺼짐이라 LED 4개가 정상 동작합니다.

**버튼은 상황에 따라 역할이 바뀝니다.**
- **평소(메뉴 등):** `config.BUTTON_MENU_ACTIONS` — 확인('a')/뒤로('b')/아래. (메인 화면의 LED는
  이제 버튼 표시 대신 **온도 색**을 보여준다 — 위 "LED 4개의 쓰임" 참고.)
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
