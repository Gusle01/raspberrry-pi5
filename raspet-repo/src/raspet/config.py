"""전역 설정 값.

해상도, GPIO 핀맵, 게임 밸런스 상수를 한곳에서 관리한다.
하드웨어 사양이 확정되면(로드맵 1단계) 이 값들을 채운다.
"""

# ── 디스플레이 ──────────────────────────────────────
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64          # 컬러 디스플레이 사용 시 128 등으로 변경
FPS = 30

# ── GPIO 핀맵 (BCM 기준, 배선 확정 후 수정) ─────────
PIN_ULTRASONIC_TRIG = None
PIN_ULTRASONIC_ECHO = None
PIN_BUZZER = None
# 조이스틱은 MCP3008 ADC의 채널 번호로 지정
ADC_CHANNEL_X = 0
ADC_CHANNEL_Y = 1

# ── 게임 밸런스 (초안) ───────────────────────────────
STAT_MAX = 100              # 능력치 상한
NEED_DECAY_PER_HOUR = 5     # 시간당 포만도/청결도 감소량
START_CURRENCY = 50         # 시작 재화

# ── 저장 ─────────────────────────────────────────────
SAVE_BACKEND = "json"       # "json" 또는 "sqlite"
SAVE_PATH = "data/savegame.json"
