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
# 기본 pygame 폰트는 한글 글리프가 없어 ???/□로 깨진다. 한글 폰트를 자동 탐색해 쓴다.
# 특정 폰트를 강제하려면 FONT_PATH에 .ttf/.ttc 경로를 지정한다(없으면 자동 탐색).
FONT_PATH = None
# 자동 탐색 시 시도할 폰트 패밀리 이름 (pygame.font.match_font 용, 우선순위 순)
FONT_CANDIDATES = [
    "notosanscjkkr", "nanumgothic", "nanumbarungothic", "notosanskr",
    "malgungothic", "applegothic", "undotum", "unbatang", "baekmukdotum",
]
FONT_SIZE = 11              # 일반 텍스트 크기
FONT_SIZE_BIG = 18         # 강조 텍스트 크기
FONT_SIZE_SMALL = 8        # 메뉴 등 항목이 많은 목록용 (실제 높이 ≈ 12px)

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

# ── 감정(무드) 임계값 ────────────────────────────────
# compute_mood가 위에서부터 검사한다(앞쪽이 우선순위 높음).
MOOD_HEALTH_SICK = 25       # 체력 이하 → 아픔
MOOD_FULLNESS_HUNGRY = 20   # 포만 이하 → 배고픔
MOOD_CLEAN_DIRTY = 20       # 청결 이하 → 더러움
MOOD_STRESS_HIGH = 70       # 스트레스 이상 → 짜증
MOOD_HAPPY = 70             # 행복 이상 → 기쁨
MOOD_SAD = 30               # 행복 이하 → 슬픔

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
