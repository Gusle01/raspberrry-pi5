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
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64          # 컬러 디스플레이 사용 시 128 등으로 변경
FPS = 30
WINDOW_SCALE = 5            # 데스크톱 미리보기 창 확대 배율 (OLED는 1로 동작)

# 색상 팔레트 (RGB) — 흑백 OLED에서는 임계값으로 이진화된다.
COLOR_BG = (8, 12, 24)
COLOR_FG = (235, 235, 245)
COLOR_ACCENT = (90, 200, 160)
COLOR_WARN = (220, 120, 90)
COLOR_DIM = (110, 120, 140)

# ── GPIO 핀맵 (BCM 기준, 배선 확정 후 수정) ─────────
PIN_ULTRASONIC_TRIG = 23
PIN_ULTRASONIC_ECHO = 24
PIN_BUZZER = 18
# 조이스틱은 MCP3008 ADC의 채널 번호로 지정
ADC_CHANNEL_X = 0
ADC_CHANNEL_Y = 1
PIN_JOYSTICK_BUTTON = 25    # 조이스틱 누름 버튼 (선택)

# ── 입력 ─────────────────────────────────────────────
JOYSTICK_DEADZONE = 0.35    # 이 값 미만의 기울기는 무시 (정규화 -1.0~1.0)

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
     "desc": "깊은 지식으로 세상의 비밀을 탐구하는 학자가 되었다."},
    {"id": "artist", "title": "예술가", "requires": {"sensitivity": 70},
     "desc": "풍부한 감수성으로 사람들의 마음을 울리는 예술가가 되었다."},
    {"id": "adventurer", "title": "모험가", "requires": {"strength": 70},
     "desc": "강인한 체력으로 미지의 세계를 누비는 모험가가 되었다."},
    {"id": "star", "title": "스타", "requires": {"charm": 70},
     "desc": "타고난 매력으로 모두의 사랑을 받는 스타가 되었다."},
    {"id": "ordinary", "title": "평범한 행복", "requires": {},
     "desc": "특출나진 않지만 평온하고 행복한 삶을 살았다."},
]

# ── 저장 ─────────────────────────────────────────────
SAVE_BACKEND = "json"       # "json" 또는 "sqlite"
SAVE_PATH = "data/savegame.json"
SAVE_DB_PATH = "data/savegame.db"
