# 🗺️ RasPet 배선 다이어그램 (한눈에 보기)

라즈베리파이 5 **40핀 헤더**에 각 모듈을 어떻게 꽂는지 그림으로 정리한 문서입니다.
핀 번호의 단일 출처는 [`src/raspet/config.py`](../src/raspet/config.py)이고,
전기적 주의사항(분압 등)은 [`hardware-wiring.md`](hardware-wiring.md)에 있습니다.

> 모든 GPIO 표기는 **BCM 번호**, 괄호 안은 **물리 핀 번호**입니다.
> Pi 5는 `RPi.GPIO`가 안 되므로 `gpiozero` + `lgpio`를 씁니다.

---

## 1. 40핀 헤더 핀맵 (■ = 이 프로젝트가 사용하는 핀)

```
                                       ■ = 사용 핀
        3V3 ■ (1) (2) ■ 5V            (1)  3V3   → MCP3008 VDD/VREF, OLED VCC, 조이스틱 VCC
  GPIO2/SDA ■ (3) (4)   5V            (2)  5V    → HC-SR04 VCC
  GPIO3/SCL ■ (5) (6) ■ GND          (3)  GPIO2 → OLED SDA
      GPIO4   (7) (8)   GPIO14        (5)  GPIO3 → OLED SCL
        GND   (9)(10)   GPIO15        (6)  GND   → OLED GND
     GPIO17  (11)(12) ■ GPIO18       (12)  GPIO18→ 부저 신호 (PWM)
     GPIO27  (13)(14) ■ GND          (14)  GND   → 부저 GND
     GPIO22  (15)(16) ■ GPIO23       (16)  GPIO23→ HC-SR04 TRIG
        3V3  (17)(18) ■ GPIO24       (18)  GPIO24→ HC-SR04 ECHO (※분압 후)
GPIO10/MOSI ■ (19)(20) ■ GND         (19)  GPIO10→ MCP3008 DIN  (MOSI)
 GPIO9/MISO ■ (21)(22) ■ GPIO25      (20)  GND   → HC-SR04 GND
GPIO11/SCLK ■ (23)(24) ■ GPIO8/CE0   (21)  GPIO9 → MCP3008 DOUT (MISO)
        GND  (25)(26)   GPIO7/CE1    (22)  GPIO25→ 조이스틱 SW(버튼)
   GPIO0/SD  (27)(28)   GPIO1/SC     (23)  GPIO11→ MCP3008 CLK
      GPIO5  (29)(30)   GND          (24)  GPIO8 → MCP3008 CS (CE0)
      GPIO6  (31)(32)   GPIO12
     GPIO13  (33)(34)   GND          ─ 여분 전원/접지 ─
     GPIO19 ■ (35)(36)  GPIO16        3V3 = 핀 1, 17   (GPIO19→DHT11 DATA)
     GPIO26  (37)(38)   GPIO20        5V  = 핀 2, 4
        GND  (39)(40)   GPIO21        GND = 핀 6,9,14,20,25,30,34,39
```

사용 핀 요약 — **전원** 1(3V3)·2(5V) / **GND** 6·14·20 / **I2C** 3·5 /
**SPI** 19·21·23·24 / **부저** 12 / **초음파** 16·18 / **조이스틱 버튼** 22 / **DHT11** 35(GPIO19).
(GND는 어느 GND 핀에 꽂아도 무방하므로 위 6·14·20은 예시입니다.)

---

## 2. 모듈별 연결도

### 2-1. OLED (SSD1306, I2C · 주소 0x3C)
```
   OLED            Pi (물리핀)
   VCC ─────────── 3V3 (1)      ※모듈이 5V 전용이면 5V(4)
   GND ─────────── GND (6)
   SDA ─────────── GPIO2 (3)
   SCL ─────────── GPIO3 (5)
```

### 2-2. 부저 (피에조, PWM 톤)
```
   Buzzer          Pi (물리핀)
   (+) 신호 ─────── GPIO18 (12)
   (−) GND ──────── GND (14)
```
> ⚠️ 코드가 `TonalBuzzer`(PWM으로 음정 재생)를 쓰므로 **수동(passive) 피에조 부저**가
> 필요합니다. 자체 발진하는 능동(active) 부저는 음정이 안 바뀝니다.

### 2-3. 초음파 HC-SR04 (ECHO 분압 필수!)
```
   HC-SR04          Pi (물리핀)
   VCC ──────────── 5V (2)
   TRIG ─────────── GPIO23 (16)          ← 직결 OK(입력 신호)
   ECHO ─[ 1kΩ ]─┬─ GPIO24 (18)          ← 5V 출력이라 반드시 분압
                 │
               [ 2kΩ ]
                 │
   GND ──────────┴─ GND (20)
```
> ECHO를 직결하면 5V가 3.3V 핀에 들어가 **GPIO가 손상**될 수 있습니다.
> 1kΩ:2kΩ 분압이면 약 3.3V로 떨어집니다.

### 2-4. 조이스틱(아날로그) + MCP3008 (SPI ADC)
Pi에는 아날로그 입력이 없어 **MCP3008 ADC**를 거칩니다.
```
        MCP3008 (16핀 DIP, 윗쪽 반원이 1번 핀 기준)
            ┌───∪───┐
  CH0  (1) ─┤       ├─ (16) VDD  ─── 3V3 (1)
  CH1  (2) ─┤       ├─ (15) VREF ─── 3V3 (1)
  CH2  (3) ─┤       ├─ (14) AGND ─── GND
  CH3  (4) ─┤ MCP   ├─ (13) CLK  ─── GPIO11 (23)
  CH4  (5) ─┤ 3008  ├─ (12) DOUT ─── GPIO9  (21)  (MISO)
  CH5  (6) ─┤       ├─ (11) DIN  ─── GPIO10 (19)  (MOSI)
  CH6  (7) ─┤       ├─ (10) CS   ─── GPIO8  (24)  (CE0)
  CH7  (8) ─┤       ├─ ( 9) DGND ─── GND
            └───────┘

   조이스틱          MCP3008 / Pi
   VCC ───────────── 3V3 (1)
   GND ───────────── GND
   VRx ───────────── CH0 (1번 핀)     → config: ADC_CHANNEL_X = 0
   VRy ───────────── CH1 (2번 핀)     → config: ADC_CHANNEL_Y = 1
   SW  ───────────── GPIO25 (22)      → config: PIN_JOYSTICK_BUTTON = 25
```
> 축이 반대로 읽히면 `src/raspet/hardware/joystick.py`의 부호/`direction()`을 조정하세요.

### 2-5. 카메라
CSI 리본 케이블을 Pi의 **전용 CSI 커넥터**에 연결(40핀 헤더 아님). `picamera2` 사용.

---

## 3. 부품 목록 (BOM)

| 부품 | 사양/모델 | 수량 | 비고 |
|---|---|---:|---|
| 라즈베리파이 5 | 4GB/8GB | 1 | |
| OLED 디스플레이 | SSD1306 128×64, **I2C**, 0x3C | 1 | SPI 모델 쓰려면 드라이버 교체 |
| ADC | **MCP3008** (10bit 8ch SPI) | 1 | 조이스틱 아날로그 입력용 |
| 아날로그 조이스틱 | 2축 + 버튼 모듈 | 1 | VRx·VRy·SW |
| 초음파 센서 | **HC-SR04** | 1 | ECHO 분압 필요 |
| 온·습도 센서 | **DHT11** (단선 디지털) | 1 | DATA→GPIO19. 베어 모듈은 풀업 4.7~10kΩ |
| 피에조 부저 | **수동(passive)** 피에조 | 1 | 능동 부저 불가 |
| 카메라 | Pi Camera (CSI) | 1 | 선택 |
| 저항 | **1kΩ, 2kΩ** | 각 1 | HC-SR04 ECHO 분압 |
| 브레드보드 | 풀/하프 | 1 | |
| 점퍼선 | M-M, M-F | 다수 | |

## 4. Fritzing 부품 목록 (도면 그릴 때 검색어)

Fritzing 부품 라이브러리에서 아래 이름으로 검색해 배치하면 됩니다.

- `Raspberry Pi 5` (없으면 `Raspberry Pi 4` 40핀 헤더로 대체 — 핀 배열 동일)
- `OLED 128x64 I2C` 또는 `SSD1306`
- `MCP3008`
- `Joystick` (analog thumb joystick)
- `HC-SR04` (Ultrasonic Distance Sensor)
- `DHT11` (Temperature Humidity Sensor)
- `Piezo Speaker` / `Piezo Buzzer`
- `Resistor` ×2 (1kΩ, 2kΩ)
- `Breadboard`

배선은 위 **2장 모듈별 연결도**의 핀 매핑을 그대로 따라 이으면 됩니다.

---

## 5. 연결 후 점검

```bash
sudo raspi-config        # Interface Options → I2C, SPI 활성화 → 재부팅
i2cdetect -y 1           # OLED가 0x3C로 보이면 I2C OK
ls /dev/spidev*          # spidev0.0 있으면 SPI OK
```
장치 인식은 [`hardware-wiring.md`](hardware-wiring.md) ✅ 절의 `available` 점검 스크립트로 확인하세요.
