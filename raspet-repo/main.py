"""RasPet 실행 진입점.

사용법:
    python main.py
"""
import sys
from pathlib import Path

# src 디렉터리를 모듈 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from raspet.app import main

if __name__ == "__main__":
    main()
