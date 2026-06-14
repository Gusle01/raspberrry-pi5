# 🚀 RasPet 실행 & GPIO 구성 가이드

PC에서 바로 돌려보는 방법부터, 라즈베리파이 5에 센서·디스플레이를 연결해
실제 게임기로 만드는 방법까지 한 번에 정리한 문서입니다.

- 배선의 **전기적 세부사항**(분압 회로 등)은 [`hardware-wiring.md`](hardware-wiring.md)를 함께 보세요.
- 모든 핀 번호·해상도 값은 [`../src/raspet/config.py`](../src/raspet/config.py)에서 관리합니다.

---

## 0. 두 가지 실행 모드

RasPet의 모든 하드웨어 접근은 추상화되어 있어, **장치가 없으면 자동으로 더미로 폴백**합니다.

| 모드 | 언제 | 방법 |
|---|---|---|
| 🖥️ **더미(PC) 모드** | 개발·테스트, 하드웨어 없이 | `RASPET_DUMMY=1` |
| 🍓 **실기(Pi) 모드** | 실제 센서·OLED 연결 | 환경변수 없이 `python main.py` |

먼저 PC에서 더미 모드로 게임을 익힌 뒤, 라즈베리파이에서 하드웨어를 붙이는 순서를 권합니다.

---

## 1. 빠른 시작 (PC, 하드웨어 불필요)

```bash
git clone https://github.com/Gusle01/raspberrry-pi5.git
cd raspberrry-pi5/raspet-repo

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install pygame Pillow numpy    # PC 미리보기에 필요한 최소 패키지

# 키보드로 조작하는 미리보기 창 실행
RASPET_DUMMY=1 python main.py
```

조작: **방향키/WASD** 이동 · **Enter/Space/Z** 확인 · **Esc/Backspace/X** 취소

> 창도 띄우지 않고 돌리려면(자동화/테스트): `RASPET_DUMMY=1 RASPET_HEADLESS=1 python main.py`

---

## 2. 라즈베리파이 5에서 실행

### 2-1. OS 및 인터페이스 준비

```bash
sudo apt update && sudo apt full-upgrade -y

# I2C(OLED) · SPI(MCP3008) 활성화
sudo raspi-config        # Interface Options → I2C 사용, SPI 사용 → 재부팅
sudo reboot
```

### 2-2. 의존성 설치

```bash
cd raspberrry-pi5/raspet-repo

# 카메라(picamera2)는 pip보다 apt 권장
sudo apt install -y python3-picamera2

# 시스템 패키지(picamera2 등)를 쓰기 위해 --system-site-packages
python3 -m venv .venv --system-site-packages
source .venv/bin/activate

pip install -r requirements.txt
```

> `MediaPipe`가 aarch64에서 설치되지 않으면 자동으로 OpenCV 손 인식으로 폴백합니다(설치 실패해도 됨).

### 2-3. GPIO 핀 팩토리 (Pi 5)

Pi 5는 `RPi.GPIO`가 동작하지 않습니다. 본 프로젝트는 `gpiozero` + **lgpio**를 씁니다.
보통 Bookworm에서는 자동 선택되지만, 문제가 있으면 명시적으로 지정하세요.

```bash
sudo apt install -y python3-lgpio
export GPIOZERO_PIN_FACTORY=lgpio
```

### 2-4. 실행

```bash
python main.py        # 환경변수 없이 = 실제 하드웨어 사용
```

조이스틱으로 이동, 조이스틱 버튼(또는 키보드)로 확인/취소합니다.
저장은 종료 시 자동으로 `data/savegame.json`에 기록됩니다.

---

## 3. GPIO 구성 (배선)

### 3-1. 핀 배정표 (BCM/GPIO 번호 기준)

| 장치 | 신호 | Pi 연결 | config 상수 |
|---|---|---|---|
| **OLED** (SSD1306, I2C) | SDA | GPIO2 (물리 3번) | I2C 고정 |
| | SCL | GPIO3 (물리 5번) | I2C 고정 |
| | 주소 | `0x3C` | `hardware/display.py` |
| **MCP3008** (SPI0) | CLK | GPIO11 (물리 23번) | SPI 고정 |
| | MISO/DOUT | GPIO9 (물리 21번) | SPI 고정 |
| | MOSI/DIN | GPIO10 (물리 19번) | SPI 고정 |
| | CS/CE0 | GPIO8 (물리 24번) | SPI 고정 |
| **조이스틱** | VRx → MCP3008 CH0 | ADC 채널 0 | `ADC_CHANNEL_X = 0` |
| | VRy → MCP3008 CH1 | ADC 채널 1 | `ADC_CHANNEL_Y = 1` |
| | SW(버튼) | GPIO25 (물리 22번) | `PIN_JOYSTICK_BUTTON = 25` |
| **초음파** (HC-SR04) | TRIG | GPIO23 (물리 16번) | `PIN_ULTRASONIC_TRIG = 23` |
| | ECHO | GPIO24 (물리 18번) ⚠분압 | `PIN_ULTRASONIC_ECHO = 24` |
| **부저**(피에조) | 신호 | GPIO18 (물리 12번) | `PIN_BUZZER = 18` |
| **카메라** | CSI 리본 | 전용 CSI 커넥터 | — |

전원: 모듈 사양에 맞춰 3.3V/5V, GND는 모두 공통 접지로 묶습니다.

### 3-2. 장치별 연결 요령

**OLED (I2C)** — VCC 3.3V, GND, SDA→GPIO2, SCL→GPIO3.
연결 확인: `i2cdetect -y 1` 에서 `3C`가 보이면 정상.

**MCP3008 + 조이스틱 (SPI)** — MCP3008의 VDD·VREF=3.3V, AGND·DGND=GND,
CLK/DOUT/DIN/CS를 위 표대로 연결. 조이스틱 VRx→CH0, VRy→CH1.
확인: `ls /dev/spidev*` 에 `spidev0.0`이 있으면 정상.

**HC-SR04 (초음파)** — VCC=**5V**, TRIG→GPIO23.
⚠️ **ECHO는 5V 출력이라 그대로 연결하면 Pi가 손상**됩니다. 저항 분압으로 3.3V로 낮추세요.

```
ECHO ──[ 1kΩ ]──┬── GPIO24
                │
              [ 2kΩ ]
                │
               GND
```

**부저** — 신호선을 GPIO18, 반대쪽 GND. (소리가 작으면 트랜지스터로 구동)

> 자세한 회로 설명·주의사항은 [`hardware-wiring.md`](hardware-wiring.md) 참고.

### 3-3. 핀을 바꾸고 싶을 때

배선을 다르게 했다면 **코드가 아니라 `config.py`만** 고치면 됩니다.

```python
# src/raspet/config.py
PIN_ULTRASONIC_TRIG = 23
PIN_ULTRASONIC_ECHO = 24
PIN_BUZZER = 18
PIN_JOYSTICK_BUTTON = 25
ADC_CHANNEL_X = 0      # 조이스틱 X축이 연결된 MCP3008 채널
ADC_CHANNEL_Y = 1      # 조이스틱 Y축 채널
```

조이스틱 방향이 반대로 읽히면 `hardware/joystick.py`의 `direction()` 부호를 배선에 맞게 조정하세요.

### 3-4. 장치 인식 점검

각 장치를 하나씩 붙여가며 `available` 플래그로 인식 여부를 확인할 수 있습니다.

```bash
cd raspberrry-pi5/raspet-repo
python3 - <<'PY'
import sys; sys.path.insert(0, "src")
from raspet.hardware.display import create_display
from raspet.hardware.joystick import create_joystick
from raspet.hardware.ultrasonic import create_ultrasonic
from raspet.hardware.buzzer import create_buzzer
from raspet.vision.camera import create_camera
print("OLED    :", create_display().available)
print("조이스틱 :", create_joystick().available)
print("초음파   :", create_ultrasonic().available)
print("부저     :", create_buzzer().available)
print("카메라   :", create_camera().available)
PY
```

`False`가 나오면 → 배선 / `raspi-config` 인터페이스 활성화 / 라이브러리 설치 / `config.py` 핀 번호를 점검하세요.

---

## 4. 조작법

| 행동 | 키보드(PC) | 실기(Pi) |
|---|---|---|
| 이동 | 방향키 / WASD | 조이스틱 기울임 |
| 확인 | Enter / Space / Z | 조이스틱 버튼 |
| 취소 | Esc / Backspace / X | (버튼 매핑) |

게임 흐름: **타이틀 → 홈(메뉴)** → 돌보기 · 미니게임 · 상점 · 탐험 · 업적 · 엔딩

---

## 5. 환경변수 정리

| 변수 | 값 | 효과 |
|---|---|---|
| `RASPET_DUMMY` | `1` | 실제 장치를 잡지 않고 더미로 동작 (PC 개발) |
| `RASPET_HEADLESS` | `1` | 창/OLED 없이 게임 루프 구동 (테스트·CI) |
| `GPIOZERO_PIN_FACTORY` | `lgpio` | Pi 5에서 GPIO 백엔드 명시 (필요 시) |

---

## 6. (선택) 부팅 시 자동 실행 — systemd

게임기처럼 전원을 켜면 바로 RasPet이 뜨게 하려면 서비스로 등록합니다.

```bash
sudo tee /etc/systemd/system/raspet.service > /dev/null <<'UNIT'
[Unit]
Description=RasPet
After=multi-user.target

[Service]
User=pi
WorkingDirectory=/home/pi/raspberrry-pi5/raspet-repo
ExecStart=/home/pi/raspberrry-pi5/raspet-repo/.venv/bin/python main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl enable --now raspet.service
```
경로(`/home/pi/...`)와 `User`는 실제 환경에 맞게 바꾸세요. 로그는 `journalctl -u raspet -f`.

---

## 7. 문제 해결

| 증상 | 점검 |
|---|---|
| `ModuleNotFoundError: pygame` | 가상환경 활성화 + `pip install -r requirements.txt` |
| OLED에 아무것도 안 나옴 | `i2cdetect -y 1`에 `3C` 확인, SDA/SCL 배선, I2C 활성화 |
| 조이스틱 값이 안 변함 | `ls /dev/spidev*`, MCP3008 배선/VREF, SPI 활성화 |
| 초음파 거리 이상/항상 같음 | TRIG/ECHO 배선, **ECHO 분압**, VCC 5V 확인 |
| GPIO 에러(Pi 5) | `export GPIOZERO_PIN_FACTORY=lgpio`, `python3-lgpio` 설치 |
| `mediapipe` 설치 실패 | 정상입니다(aarch64 미지원). 무시하면 OpenCV로 자동 폴백됩니다. |
| `import cv2` → `libGL.so.1` 없음 | `sudo apt install -y libgl1`, 또는 `pip install opencv-python-headless` |
| 손 인식 안 됨 | 조명 밝게, MediaPipe 미설치 시 OpenCV 폴백(정확도↓) |
| 하드웨어 없이 그냥 돌리고 싶음 | `RASPET_DUMMY=1 python main.py` |
