"""pytest 공통 설정.

- src 디렉터리를 모듈 경로에 추가한다.
- 테스트는 항상 더미 하드웨어 + 헤드리스로 동작하도록 환경변수를 강제한다
  (raspet.config 가 임포트 시점에 이 값을 읽으므로 가장 먼저 설정).
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("RASPET_DUMMY", "1")
os.environ.setdefault("RASPET_HEADLESS", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
