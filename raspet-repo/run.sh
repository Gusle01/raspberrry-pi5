#!/usr/bin/env bash
# RasPet 실행 런처 — 반드시 venv 파이썬으로 돌려야 카메라 게임(프리뷰 창·손 인식·
# 색 검출)에 필요한 OpenCV(cv2)가 잡힌다. 시스템 python3에는 cv2가 없다.
#
# 사용법:  ./run.sh            # 일반 실행
#          ./run.sh --dummy    # 하드웨어 없이(PC) 더미로 실행
set -euo pipefail
cd "$(dirname "$0")"

VENV_PY="../.venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
    echo "[RasPet] venv를 찾지 못했습니다($VENV_PY)." >&2
    echo "         프로젝트 루트에서 'python3 -m venv .venv --system-site-packages' 후" >&2
    echo "         '.venv/bin/pip install -r raspet-repo/requirements.txt'를 실행하세요." >&2
    exit 1
fi

if [[ "${1:-}" == "--dummy" ]]; then
    export RASPET_DUMMY=1
fi

exec "$VENV_PY" main.py
