"""전역 설정 값.

해상도, GPIO 핀맵, 게임 밸런스 상수를 한곳에서 관리한다.
하드웨어 사양이 확정되면(로드맵 1단계) 이 값들을 채운다.

원칙: 핀 번호·해상도·밸런스 수치는 코드에 하드코딩하지 말고 반드시 여기서 가져온다.
"""
import os

# ── 실행 모드 ────────────────────────────────────────
# 환경변수 RASPET_DUMMY=1 이면 실제 장치를 잡지 않고 더미로 동작한다.
# (주변장치가 연결되지 않은 Pi/PC에서 개발·테스트할 때 사용)
USE_DUMMY_HARDWARE = os.environ.get("RASPET_DUMMY", "0") == "1"
# 환경변수 RASPET_HEADLESS=1 이면 창/OLED 없이 게임 루프를 돌린다(테스트용).
HEADLESS = os.environ.get("RASPET_HEADLESS", "0") == "1"

# ── 디스플레이 ──────────────────────────────────────
# 디자인(가상 캔버스) 해상도 = OLED 실해상도.
# 모든 씬은 이 크기의 고정 캔버스에만 그린다. 창/OLED 출력은 이 캔버스를
# 스케일/전송만 할 뿐이므로, 좌표는 항상 GAME_W·GAME_H(=ctx.width·height) 기준으로 쓴다.
GAME_W = 128
GAME_H = 64                 # 컬러 디스플레이 사용 시 128 등으로 변경
FPS = 30

# 데스크톱 미리보기 초기 창 크기. 창은 자유롭게 리사이즈 가능하며,
# 캔버스는 창 안에 비율 유지·정수배로 확대(레터박스)되어 표시된다. OLED 출력은 이 값과 무관.
WINDOW_SCALE = 8           # 초기 창 = 캔버스의 이 배율 (예: 8 → 1024×512)
WINDOW_W = GAME_W * WINDOW_SCALE   # 1024
WINDOW_H = GAME_H * WINDOW_SCALE   # 512
WINDOW_RESIZABLE = True    # 창 크기 조절 허용 (모서리 드래그)
# 환경변수 RASPET_FULLSCREEN=1 이면 전체화면으로 시작 (게임 중 F11로도 토글)
FULLSCREEN = os.environ.get("RASPET_FULLSCREEN", "0") == "1"

# 하위 호환 별칭 — 기존 코드/외부 참조가 SCREEN_WIDTH/HEIGHT를 쓸 수 있어 유지한다.
SCREEN_WIDTH = GAME_W
SCREEN_HEIGHT = GAME_H

# 색상 팔레트 (RGB) — 흑백 OLED에서는 임계값으로 이진화된다.
COLOR_BG = (8, 12, 24)
COLOR_FG = (235, 235, 245)
COLOR_ACCENT = (90, 200, 160)
COLOR_WARN = (220, 120, 90)
COLOR_DIM = (110, 120, 140)

# ── 폰트 (한글 표시) ─────────────────────────────────
# 작은 OLED(128×64)에서 한글이 또렷하게 보이도록, 픽셀(비트맵) 한글 폰트 Galmuri를
# repo에 번들해 기본으로 쓴다. 아웃라인 폰트(Noto 등)는 8~11px에서 획이 뭉개진다.
# 번들 파일이 없으면 아래 FONT_CANDIDATES 자동 탐색으로 폴백한다.
_FONT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..",
                                          "assets", "fonts"))
# 역할별 폰트 파일. 같은 크기를 유지하되 픽셀 폰트로 또렷하게 그린다.
FONT_FILE = os.path.join(_FONT_DIR, "Galmuri11.ttf")        # 본문(11px)
FONT_FILE_BIG = os.path.join(_FONT_DIR, "Galmuri11.ttf")    # 강조(18px)
FONT_FILE_SMALL = os.path.join(_FONT_DIR, "Galmuri7.ttf")   # 작은 목록(8px)
# 픽셀 폰트는 안티앨리어싱을 끄면 더 또렷하다(흑백 OLED 전송 시에도 깔끔).
FONT_ANTIALIAS = False
# 강제 폰트 경로(있으면 위 번들보다 우선). 자동 탐색용 폴백 패밀리 이름도 둔다.
FONT_PATH = None
FONT_CANDIDATES = [
    "notosanscjkkr", "nanumgothic", "nanumbarungothic", "notosanskr",
    "malgungothic", "applegothic", "undotum", "unbatang", "baekmukdotum",
]
FONT_SIZE = 11              # 일반 텍스트 크기
FONT_SIZE_BIG = 18         # 강조 텍스트 크기
FONT_SIZE_SMALL = 8        # 메뉴 등 항목이 많은 목록용

# ── GPIO 핀맵 (BCM 기준, 배선 확정 후 수정) ─────────
PIN_ULTRASONIC_TRIG = 23
PIN_ULTRASONIC_ECHO = 24
PIN_BUZZER = 18
# 조이스틱은 MCP3008 ADC의 채널 번호로 지정 (실제 배선: VRx=CH2, VRy=CH1)
ADC_CHANNEL_X = 2
ADC_CHANNEL_Y = 1
# 조이스틱 누름(SW)을 읽는 방식.
#  • ADC_CHANNEL_BUTTON 가 None 이 아니면: SW를 MCP3008의 그 채널(아날로그)에서 읽는다.
#  • None 이면: PIN_JOYSTICK_BUTTON(GPIO 디지털, 내장 풀업)로 읽는다.
# ⚠ 실측 결과 SW를 풀업 없이 MCP3008 CH0로 읽으면 안 눌러도 값이 0.0~0.98로 떠다녀
#   (floating) 눌림/뗌 구분이 불가능했다. → 기본은 None(GPIO)로 둔다. ADC로 쓰려면
#   SW와 3.3V 사이에 풀업저항(약 10kΩ)을 달고 아래를 0(=CH0)으로 되돌리면 된다.
ADC_CHANNEL_BUTTON = None
ADC_BUTTON_PRESSED_BELOW = 0.5   # ADC SW 값이 이 미만이면 '눌림'으로 본다(풀업 장착 시)
PIN_JOYSTICK_BUTTON = 25    # ADC_CHANNEL_BUTTON 가 None 일 때 사용하는 GPIO 핀(내장 풀업)
# 두더지 잡기용 LED·버튼 (BCM). 사용 중 핀(I2C 2·3, 부저 18, 초음파 23·24, 조이스틱 25,
# SPI 7~11)과 겹치지 않게 배치. 위치(왼/가운데/오른쪽)는 버튼 ←↓→에 대응한다.
PIN_LEDS = [5, 6, 13, 19]   # LED 4개 (각 220~330Ω 저항 → LED → GND). 5·6·13=기존 3구멍,
                            # 19=파랑(추가, 예전 DHT11 자리). 메인화면 온도색·색깔찾기 힌트에 쓴다.
PIN_BUTTONS = [16, 20, 21]  # 두더지 버튼 3개 (버튼 → GND, 내부 풀업 사용)
# LED와 버튼은 같은 인덱스(0·1·2)끼리 한 쌍으로 본다(4번째 파랑 LED는 버튼 짝 없음). 각 자리에
# 실제로 꽂은 LED 색을 적어두고(배선에 맞게 수정), 이 색으로 버튼 기능을 지정한다(BUTTON_MENU_ACTIONS).
LED_COLORS = ["green", "red", "yellow", "blue"]   # PIN_LEDS 자리의 LED 색
# 온도 → LED 색(메인 화면). 얼굴 표정과 함께 색으로도 더위/추위를 알린다(센서 없으면 소등).
TEMP_LED_HOT = "red"        # TEMP_HOT_ABOVE_C 이상 → 빨강
TEMP_LED_OK = "green"       # 쾌적 범위 → 초록
TEMP_LED_COLD = "blue"      # TEMP_COLD_BELOW_C 이하 → 파랑

# ── 4자리 7세그먼트 LED (74HC595 + 자릿수 멀티플렉싱) ─────
# 메인 화면=주변 온도, 시간제한 게임=남은 시간 표시. RASPET_7SEG=1로 켤 수 있다.
# ※ 기본은 꺼짐(LED 4개를 쓰기 위함). 켜면 LED 핀(5·6·13·19)을 세그먼트/래치로
#   재사용하므로 그땐 LED를 달지 않는다(app.build_hardware가 LED를 더미로 둔다).
#   자릿수 GPIO4는 1-Wire(w1-gpio) 오버레이를 꺼야 쓸 수 있다(docs/hardware-wiring.md 3-4 참고).
#   ※ 7세그는 자릿수 공통선마다 트랜지스터가 필요(과전류) — 없으면 켜지 말 것.
SEG_ENABLED = os.environ.get("RASPET_7SEG", "0") == "1"
PIN_7SEG_DATA = 14          # 74HC595 DS(데이터)    — 시리얼 콘솔이 꺼져 있어야 GPIO로 쓸 수 있음
PIN_7SEG_CLOCK = 15         # 74HC595 SHCP(시프트클럭)
PIN_7SEG_LATCH = 19         # 74HC595 STCP(래치)
# 자릿수 0~3 공통선. ※ GPIO 직결 금지 — 자릿수마다 NPN 트랜지스터로 받는다(과전류 방지).
PIN_7SEG_DIGITS = [5, 6, 13, 4]
# 74HC595 출력(시프트 순서: 처음 나가는 비트=MSB) → 세그먼트 대응. 배선이 다르면 여기만 고친다.
SEG_ORDER = ["a", "b", "c", "d", "e", "f", "g", "dp"]
SEG_DIGIT_ON_LEVEL = 1      # NPN 싱크 기준: GPIO HIGH일 때 그 자릿수 ON (공통 애노드+PNP면 0)
SEG_DWELL_S = 0.002         # 자릿수당 점등 시간(작을수록 어둡고, 너무 크면 깜빡임). 4자리×=약 125Hz

# ── 4×4 매트릭스 키패드 ──────────────────────────────────
# 16키 키패드. 활성화하면 기존 푸시버튼(PIN_BUTTONS=16·20·21)을 대체하며, 그 핀을
# 열(col)로 재사용한다(→ 키패드 사용 시 별도 3버튼은 달지 않는다). 환경변수 RASPET_KEYPAD=0으로 끌 수 있다.
KEYPAD_ENABLED = os.environ.get("RASPET_KEYPAD", "1") == "1"
PIN_KEYPAD_ROWS = [26, 17, 27, 22]    # 행(BCM, 출력) — GPIO4는 1-Wire(w1-gpio)가 써서 26으로 대체
PIN_KEYPAD_COLS = [12, 16, 20, 21]    # 열(BCM, 입력·풀업) — 16·20·21은 기존 3버튼 핀 재사용
# 키 라벨(행×열). 게임/메뉴에서 위치·라벨로 참조한다.
KEYPAD_LAYOUT = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"],
]
# 평소(메뉴) 화면에서 키패드 키 → 행동. 조이스틱이 없어도 키패드만으로 메뉴를 쓸 수 있게.
# 사용자 지정 물리 스위치 배치(모듈 실크 S1~S16, 행 우선):
#   S11=위, S14=왼쪽, S15=아래, S16=오른쪽 (S11 아래에 S14·S15·S16 → 방향키 모양),
#   S4=확인, S1=뒤로. 아래 라벨은 KEYPAD_LAYOUT에서 각 스위치 자리의 라벨이다.
KEYPAD_MENU_ACTIONS = {
    "9": "up",      # S11 (2,2)
    "0": "left",    # S14 (3,1)
    "#": "down",    # S15 (3,2)
    "D": "right",   # S16 (3,3)
    "A": "a",       # S4  (0,3) 확인
    "1": "b",       # S1  (0,0) 뒤로
}
KEYPAD_BACK_KEY = "1"     # 게임 중 이 키(S1) = 뒤로/종료

# ── 환경 센서 (조도 + 온도, 로드맵 확장) ─────────────────
# 조도센서(LDR)는 조이스틱과 같은 MCP3008(SPI)의 빈 채널에 연결한다(CH1=VRy, CH2=VRx).
ADC_CHANNEL_LIGHT = 3
# 조도값(0.0=캄캄 ~ 1.0=매우 밝음) 판정 기준.
# 실측 보정(이 LDR+분압 기준): 센서를 가리면 ~0.00~0.02, 일반 실내 ~0.08~0.21,
# 손전등 직사 ~0.40(최대). 손전등을 직접 비춰도 0.45까지 안 올라가므로 기준을 낮춘다.
# day/night 판정은 is_dark()의 LIGHT_DARK_BELOW 하나만 사용한다(아래 ABOVE는 미사용).
LIGHT_DARK_BELOW = 0.05     # 이 값 이하로 어두워지면(가림/소등) '밤'으로 보고 펫이 잠든다
LIGHT_LIGHT_ABOVE = 0.10    # (현재 코드 미사용) 향후 히스테리시스용 상단 기준
# 분압 배선(LDR-저항 위치)에 따라 밝을수록 ADC 값이 작아질 수 있다. True면 값을 반전한다.
LIGHT_INVERT = False

# BMP180(온도+기압) — I2C. ※ 습도 측정 기능은 없다. 습도까지 원하면 BME280로 교체한다.
BMP180_I2C_BUS = 1
BMP180_I2C_ADDR = 0x77
BMP180_OVERSAMPLING = 1     # 0~3 (클수록 정밀하지만 느림)
# 온도 쾌적 범위(℃). 이 범위를 벗어나면 캐릭터가 더워/추워한다.
TEMP_COLD_BELOW_C = 15      # 이하 → 추워요
TEMP_HOT_ABOVE_C = 30       # 이상 → 더워요
# 습도(현재 BMP180엔 없음 → None). BME280 등을 달면 이 임계값으로 '끈적함'을 표현할 수 있다.
HUMID_HIGH_ABOVE = 70       # % 이상 (향후 사용)

# 환경 센서 폴링 주기(ms). 매 프레임 I2C/ADC를 읽지 않도록 제한한다.
ENV_POLL_MS = 1000

# ── 카메라 미리보기 창 (카메라 미니게임용) ───────────────
# 가위바위보·색깔 찾기처럼 카메라를 쓰는 미니게임 중, 실제 카메라 화면을 별도 창으로
# 띄운다(OLED/게임 창에는 128×64 게임 화면, 이 창에는 카메라 원본). cv2가 있어야 동작.
CAMERA_PREVIEW = True
CAMERA_PREVIEW_TITLE = "RasPet Camera"
CAMERA_PREVIEW_SIZE = (320, 240)   # 미리보기 창 크기(픽셀)

# ── 입력 ─────────────────────────────────────────────
JOYSTICK_DEADZONE = 0.35    # 이 값 미만의 기울기는 무시 (정규화 -1.0~1.0)
JOYSTICK_INVERT_Y = True    # 배선상 위/아래가 반대로 잡혀서 y축을 뒤집는다(밀어 올리면 'up')

# 메뉴 등 평소 화면에서 '색'별 버튼이 하는 행동. 초록=확인, 빨강=뒤로(요청 사항).
#   "a"=확인, "b"=뒤로, "up"/"down"/"left"/"right"=메뉴 이동, None=없음
# (조이스틱은 이동+누름 확인을 담당하고, 버튼은 확인/뒤로를 보조한다.)
BUTTON_MENU_ACTIONS = {"green": "a", "red": "b", "yellow": "down"}
# 두더지 잡기 중에는 위 매핑을 무시하고 3버튼 모두 구멍(왼·가운데·오른쪽)으로만 쓴다.
BUTTON_GAME_ACTIONS = ["left", "down", "right"]
# 평소 화면에서 확인/뒤로 버튼의 LED를 켜 어떤 버튼인지 알려줄지 여부.
BUTTON_LED_INDICATORS = True

# ── 게임 밸런스 (초안) ───────────────────────────────
STAT_MAX = 100              # 능력치 상한
NEED_DECAY_PER_HOUR = 5     # 시간당 포만도/청결도 감소량
NEGLECT_HAPPINESS_PENALTY = 2   # 포만/청결이 바닥일 때 시간당 행복/체력 추가 하락
START_CURRENCY = 50         # 시작 재화

# 돌봄 행동 효과
FEED_FULLNESS = 25         # 먹이 주기 → 포만도
FEED_HAPPINESS = 3
CLEAN_CLEANLINESS = 35     # 씻기기 → 청결도
PLAY_HAPPINESS = 12        # 놀아주기 → 행복도
PLAY_STRESS_RELIEF = 8     # 놀아주기 → 스트레스 감소

# ── 하루(일수) & 방치 엔딩 ───────────────────────────
# 돌보기 행동(먹이/씻기/놀기/훈련) 1회 = 하루. 메인 화면에 D+일수로 표시한다.
DAY_FULLNESS_DECAY = 8       # 하루가 지날 때 포만도 자동 감소
DAY_CLEANLINESS_DECAY = 6    # 하루가 지날 때 청결도 자동 감소
DAY_NEGLECT_HAPPINESS = 10   # 포만/청결이 바닥인 날엔 행복도 추가 하락
NEGLECT_ENDING_DAYS = 3      # 포만/청결/행복이 연속 이 일수만큼 0이면 방치 엔딩
# 방치/스트레스로 인한 강제(나쁜) 엔딩. 발생하면 화면 표시 후 새 세대로 초기화된다.
FORCED_ENDINGS = {
    "fullness":    {"id": "thief",    "title": "도둑",
                    "desc": "굶주림에 지쳐 도둑이 되어 떠났다."},
    "cleanliness": {"id": "sick",     "title": "질병",
                    "desc": "더러움 속에 병들어 앓다가 떠나갔다."},
    "happiness":   {"id": "wanderer", "title": "방랑자",
                    "desc": "행복을 잃고 정처 없이 떠도는 방랑자가 됐다."},
    "stress":      {"id": "runaway",  "title": "가출",
                    "desc": "쌓인 스트레스에 집을 뛰쳐나갔다."},
}

# 능력치 훈련 효과 (스트레스가 높으면 효율 감소)
TRAIN_AMOUNT = 6
STRESS_PER_TRAIN = 5
# 스트레스 50 이상이면 성장 효율이 절반으로 떨어진다.
STRESS_PENALTY_THRESHOLD = 50
STRESS_PENALTY_FACTOR = 0.5

# ── 성장 단계(진화) ──────────────────────────────────
# 누적 능력치 합이 임계값을 넘으면 다음 단계로 진화한다.
STAGE_THRESHOLDS = [0, 80, 160, 280]   # 단계 0~3 진입에 필요한 능력치 총합

# ── 오목 ─────────────────────────────────────────────
OMOK_BOARD_SIZE = 15        # 판 크기 (가로=세로)
OMOK_WIN_LENGTH = 5         # 승리에 필요한 연속 돌 수
OMOK_WIN_REWARD = 30        # 승리 시 재화
OMOK_DRAW_REWARD = 10       # 무승부 시 재화
OMOK_LOSE_REWARD = 5        # 패배 시 위로 재화

# ── 가위바위보 ───────────────────────────────────────
RPS_ROUNDS = 3             # 3판 2선승
RPS_WIN_REWARD = 8         # 라운드 승리당 재화
RPS_MATCH_BONUS = 10       # 매치(세트) 승리 보너스
RPS_CAMERA_SECONDS = 5     # 영상 미리보기 카운트다운(초). 0이 되는 순간 프레임을 캡처해 그 손으로 판정한다.
RPS_CAPTURE_SAMPLES = 7    # 캡처 시 모을 프레임 수. 여러 장을 다수결로 합쳐 오인식을 줄인다.

# ── 스네이크 ─────────────────────────────────────────
SNAKE_COLS = 16
SNAKE_ROWS = 12
SNAKE_TICK_MS = 160        # 한 칸 이동 간격(ms)
SNAKE_REWARD_PER_FOOD = 3

# ── 초음파 점프 ──────────────────────────────────────
# 손 거리(cm)를 캐릭터 높이로 매핑한다. 가까울수록 높이 점프.
JUMP_DISTANCE_MIN_CM = 5    # 이보다 가까우면 최대 점프
JUMP_DISTANCE_MAX_CM = 40   # 이보다 멀면 바닥
JUMP_REWARD_PER_OBSTACLE = 2
JUMP_OBSTACLE_INTERVAL_MS = 1400
# 위·아래 파이프 사이 통과 구멍 크기(정규화 0~1). 플레이어(높이 ≈0.14)보다 넉넉히 크게
# 둬 항상 통과 가능. 구멍 위치가 매번 달라 위·아래 파이프 길이도 제각각이 된다.
JUMP_GAP_MIN = 0.40
JUMP_GAP_MAX = 0.52

# ── 색깔 찾기 ────────────────────────────────────────
COLOR_HUNT_ROUNDS = 3
COLOR_HUNT_REWARD_PER_ROUND = 6
COLOR_HUNT_TIME_LIMIT_S = 10
# 인식 대상 색 (이름, HSV 하한, HSV 상한) — OpenCV HSV 기준(H:0~179)
COLOR_HUNT_TARGETS = [
    ("빨강", (0, 120, 70), (10, 255, 255)),
    ("초록", (40, 80, 70), (80, 255, 255)),
    ("파랑", (100, 120, 70), (130, 255, 255)),
    ("노랑", (20, 120, 120), (35, 255, 255)),
]
# 타깃 색 이름 → 켤 LED 색(LED_COLORS 중). 흑백 OLED가 못 보여주는 실제 색을 LED로 힌트한다.
COLOR_HUNT_LED = {"빨강": "red", "초록": "green", "파랑": "blue", "노랑": "yellow"}

# ── 두더지 잡기 (LED 3 + 버튼 3, 반응 게임) ───────────
WHACK_DURATION_S = 30          # 제한 시간(초) — 시간제
WHACK_TIMEOUT_START_S = 1.2    # 두더지 1마리 생존 시간(시작) → 점점 짧아짐
WHACK_TIMEOUT_END_S = 0.5      # 두더지 생존 시간(종료 시점)
WHACK_SPAWN_START_S = 0.9      # 다음 두더지 등장 간격(시작)
WHACK_SPAWN_END_S = 0.45       # 등장 간격(종료 시점)
WHACK_DOUBLE_AFTER_S = 15      # 이 시점 이후 동시 2마리 등장 허용(고난도)
WHACK_TRAP_AFTER_S = 8         # 함정(누르면 안 되는 LED) 등장 시작 시점
WHACK_TRAP_CHANCE = 0.22       # 등장 시 함정일 확률
WHACK_HIT_REWARD = 1           # 명중 1회당 재화(점수)
WHACK_COMBO_STEP = 5           # 콤보 이 단위마다 보너스 1칸 증가
WHACK_COMBO_BONUS = 1          # 콤보 보너스 칸당 추가 재화
WHACK_TRAP_PENALTY = 2         # 함정을 눌렀을 때 차감 재화(0 미만으로는 안 내려감)
# 4×4 키패드가 연결돼 있으면 OLED에 이 크기의 격자를 그리고 키패드로 두더지를 잡는다.
# 키패드가 없으면 기존 3구멍(좌·가운데·우, 버튼/방향키) 모드로 자동 폴백한다.
WHACK_GRID_ROWS = 4
WHACK_GRID_COLS = 4

# ── 상점 품목 (카테고리/가격/효과) ───────────────────
# effect: 캐릭터 능력치/상태에 더해질 값(dict). costume은 외형 키만 부여.
SHOP_ITEMS = [
    {"id": "snack", "name": "간식", "price": 12, "category": "consumable",
     "effect": {"fullness": 15, "happiness": 6}},
    {"id": "soap", "name": "비누", "price": 10, "category": "consumable",
     "effect": {"cleanliness": 30}},
    {"id": "toy", "name": "장난감", "price": 20, "category": "consumable",
     "effect": {"happiness": 18, "stress": -12}},
    {"id": "book", "name": "책", "price": 25, "category": "function",
     "effect": {"intellect": 8}},
    {"id": "dumbbell", "name": "아령", "price": 25, "category": "function",
     "effect": {"strength": 8}},
    {"id": "hat", "name": "모자", "price": 30, "category": "costume",
     "effect": {"charm": 5}},
    {"id": "cape", "name": "망토", "price": 45, "category": "costume",
     "effect": {"charm": 9}},
]

# ── 엔딩 분기 ────────────────────────────────────────
# 우선순위 순서대로 평가하여 최초로 조건을 만족하는 엔딩을 채택한다.
# requires: 해당 능력치가 값 이상이면 충족. 마지막 항목은 기본(fallback) 엔딩.
ENDINGS = [
    {"id": "scholar", "title": "학자", "requires": {"intellect": 70},
     "desc": "깊은 지식으로 세상을 탐구하는 학자가 됐다."},
    {"id": "artist", "title": "예술가", "requires": {"sensitivity": 70},
     "desc": "풍부한 감수성으로 마음을 울리는 예술가가 됐다."},
    {"id": "adventurer", "title": "모험가", "requires": {"strength": 70},
     "desc": "강인한 힘으로 세계를 누비는 모험가가 됐다."},
    {"id": "star", "title": "스타", "requires": {"charm": 70},
     "desc": "타고난 매력으로 사랑받는 스타가 됐다."},
    {"id": "ordinary", "title": "평범한 행복", "requires": {},
     "desc": "특출나진 않아도 평온하고 행복하게 살았다."},
]

# ── 감정(무드) 규칙 ──────────────────────────────────
# 표정 집합과 상태→표정 매핑을 데이터로 정의한다(코드에 임계값을 박지 않는다).
# compute_mood가 위에서부터 검사해 조건을 모두 만족하는 첫 규칙을 채택한다(앞쪽=우선순위 높음).
#   when: (signal, op, value) 조건들의 AND 목록. 전부 참이면 그 무드.
#   signal: 캐릭터 속성명(health/fullness/cleanliness/stress/happiness) 또는 "period"(시간대).
#   op: "<=" ">=" "==" "<" ">"
# 새 표정을 추가하려면 여기 한 줄(+ sprite.py에 얼굴 하나)만 더하면 된다.
MOODS = [
    {"id": "sick",     "label": "아파요",     "when": [("health", "<=", 25)]},
    # 어두우면(조도센서) 펫이 잠든다. 아픈 경우만 빼고 수면이 우선이라 sick 바로 아래.
    {"id": "asleep",   "label": "쿨쿨...",    "when": [("asleep", "==", True)]},
    {"id": "hungry",   "label": "배고파요",   "when": [("fullness", "<=", 20)]},
    {"id": "dirty",    "label": "지저분해요", "when": [("cleanliness", "<=", 20)]},
    # 주변 온도(BMP180)에 따라 더워/추워한다. 값이 없으면(센서 미연결) 매칭 안 됨.
    {"id": "hot",      "label": "더워요",     "when": [("temperature_c", ">=", TEMP_HOT_ABOVE_C)]},
    {"id": "cold",     "label": "추워요",     "when": [("temperature_c", "<=", TEMP_COLD_BELOW_C)]},
    {"id": "stressed", "label": "짜증나요",   "when": [("stress", ">=", 70)]},
    # 외로움(방치): 행복이 바닥인데 배도 곯은 상태 → 단순 우울(sad)과 구분, sad보다 우선.
    {"id": "lonely",   "label": "외로워요",   "when": [("happiness", "<=", 20),
                                                       ("fullness", "<=", 50)]},
    {"id": "happy",    "label": "행복해요",   "when": [("happiness", ">=", 70)]},
    {"id": "sad",      "label": "우울해요",   "when": [("happiness", "<=", 30)]},
    # 졸림: 밤이고 긴급/감정 상태가 아닐 때(우선순위 낮음).
    {"id": "sleepy",   "label": "졸려요",     "when": [("period", "==", "night")]},
    # 기본값(빈 조건 → 항상 매칭하므로 반드시 마지막).
    {"id": "neutral",  "label": "그저그래요", "when": []},
]
# 상태로 자동 선택되지 않고 이벤트로만 쓰이는 무드(예: 레벨업 직후의 '신남').
MOOD_LABELS_EXTRA = {"excited": "신나요!"}

# ── XP / 레벨 (전체 진행도 레이어) ───────────────────
# 기존 능력치·진화(stage)와 별개로 "얼마나 함께 시간을 보냈는가"를 나타내는 누적 지표.
# 행동별 XP 획득량(데이터). 적립 위치는 scenes.play_and_reward / CareScene 참고.
XP_REWARDS = {
    "minigame_play": 2,    # 미니게임 참가(결과 무관)
    "minigame_win": 8,     # 미니게임 승리(보상 > 0) — 참가와 합쳐 약 +10
    "care": 4,             # 돌보기(먹이/씻기/놀기)
    "train": 5,            # 능력치 훈련
}
# 레벨 곡선: 레벨 L→L+1 에 필요한 XP = XP_LEVEL_BASE + (L-1)*XP_LEVEL_STEP.
# 누적 임계값은 progression.py가 이 상수로 계산한다(수치만 바꾸면 곡선이 바뀐다).
XP_LEVEL_BASE = 40
XP_LEVEL_STEP = 25
XP_MAX_LEVEL = 20
# 마일스톤 타이틀(해당 레벨 이상이면 그 타이틀 사용). 새 타이틀은 한 줄 추가로 확장.
LEVEL_TITLES = {
    1: "갓난아기", 3: "아기", 5: "어린이",
    8: "청소년", 12: "어른", 16: "베테랑", 20: "전설",
}

# 성장 단계별 몸 색 (stage 0~3)
STAGE_COLORS = [
    (230, 220, 180),   # 0: 알
    (150, 210, 230),   # 1: 아기
    (120, 200, 150),   # 2: 어린이
    (200, 170, 230),   # 3: 어른
]

# ── 시간대 (시간대 반영) ─────────────────────────────
# (시작시각, 종료시각) 반열린구간 [start, end). 나머지는 'night'.
DAYTIME_BOUNDS = {"morning": (6, 11), "day": (11, 18), "evening": (18, 21)}
DAYTIME_TINT = {
    "morning": (30, 28, 40),
    "day": (12, 18, 34),
    "evening": (38, 22, 30),
    "night": (6, 8, 18),
}

# ── 랜덤 이벤트 ──────────────────────────────────────
EVENT_CHANCE = 0.35         # 미니게임 후 이벤트가 발생할 확률
# weight: 가중치(클수록 자주). effect: 캐릭터에 적용할 변화.
EVENTS = [
    {"id": "found_coin", "title": "행운", "weight": 3,
     "desc": "길에서 동전을 주웠다!", "effect": {"currency": 10}},
    {"id": "nice_weather", "title": "맑은 날", "weight": 3,
     "desc": "기분 좋은 바람이 분다.", "effect": {"happiness": 8, "stress": -5}},
    {"id": "good_dream", "title": "좋은 꿈", "weight": 2,
     "desc": "개운하게 일어났다.", "effect": {"stress": -10}},
    {"id": "caught_cold", "title": "감기", "weight": 2,
     "desc": "으슬으슬 감기에 걸렸다...", "effect": {"health": -10, "happiness": -5}},
    {"id": "spark", "title": "영감", "weight": 1,
     "desc": "문득 깨달음을 얻었다!", "effect": {"intellect": 5}},
    {"id": "workout", "title": "의욕", "weight": 1,
     "desc": "운동이 잘 됐다!", "effect": {"strength": 5}},
    {"id": "fan_letter", "title": "팬레터", "weight": 1,
     "desc": "누군가 편지를 보내왔다.", "effect": {"charm": 4, "happiness": 5}},
]

# ── 도전 과제(업적) ──────────────────────────────────
# requires: 캐릭터 속성(또는 'stat_total')이 값 이상이면 달성.
ACHIEVEMENTS = [
    {"id": "first_game", "title": "첫 걸음", "desc": "미니게임을 처음 즐겼다.",
     "requires": {"games_played": 1}},
    {"id": "evolved", "title": "성장", "desc": "처음으로 진화했다.",
     "requires": {"stage": 1}},
    {"id": "rich", "title": "부자", "desc": "재화를 200 모았다.",
     "requires": {"currency": 200}},
    {"id": "scholar_path", "title": "수재", "desc": "지력 80을 달성했다.",
     "requires": {"intellect": 80}},
    {"id": "all_rounder", "title": "팔방미인", "desc": "핵심 능력치 합 200.",
     "requires": {"stat_total": 200}},
    {"id": "veteran", "title": "베테랑", "desc": "미니게임을 20판 했다.",
     "requires": {"games_played": 20}},
]

# ── 저장 ─────────────────────────────────────────────
SAVE_BACKEND = "json"       # "json" 또는 "sqlite"
SAVE_PATH = "data/savegame.json"
SAVE_DB_PATH = "data/savegame.db"
