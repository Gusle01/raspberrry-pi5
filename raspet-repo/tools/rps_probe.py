#!/usr/bin/env python3
"""가위바위보 손 인식 실측 진단 (OpenCV 백엔드).

카메라로 손을 잡아 매 프레임 분류 결과와 *중간 신호값*(면적·solidity·골 개수)을
함께 출력한다. 주먹/가위/보를 차례로 들어보며 solidity·defect 임계값을
실측 보정하는 용도다. 게임과 똑같은 HandRecognizer.analyze_opencv 를 쓴다.

실행:  cd raspet-repo && python3 tools/rps_probe.py [프레임수]
중단:  Ctrl-C
"""
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from raspet.vision.hand import HandRecognizer, fingers_to_gesture  # noqa: E402

_KO = {"rock": "바위✊", "scissors": "가위✌", "paper": "보✋", None: "실패"}


def _open_camera():
    """picamera2 우선, 없으면 rpicam-still 폴백으로 프레임 공급자를 만든다."""
    try:
        from picamera2 import Picamera2
        if Picamera2.global_camera_info():
            cam = Picamera2()
            cam.configure(cam.create_preview_configuration(
                main={"format": "RGB888", "size": (640, 480)}))
            cam.start()
            time.sleep(0.5)  # AE/AWB 안정화
            print("[probe] picamera2 사용")
            return (lambda: cam.capture_array()), cam.stop
    except Exception as e:
        print(f"[probe] picamera2 불가({e}) → rpicam-still 폴백")

    import subprocess
    import cv2

    def grab():
        out = "/tmp/rps_probe.jpg"
        subprocess.run(
            ["rpicam-still", "-n", "--immediate", "-t", "1",
             "--width", "640", "--height", "480", "-o", out],
            check=True, capture_output=True)
        img = cv2.imread(out)
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if img is not None else None

    return grab, (lambda: None)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    rec = HandRecognizer(use_mediapipe=False)  # 이 Pi엔 mediapipe 없음 → opencv 고정
    print(f"[probe] backend={rec.backend}  프레임 {n}장 캡처 (Ctrl-C 중단)")
    print(f"[probe] 임계값 area>{HandRecognizer.OPENCV_MIN_AREA} "
          f"solidity>{HandRecognizer.OPENCV_ROCK_SOLIDITY} "
          f"defect_depth>{HandRecognizer.OPENCV_DEFECT_DEPTH}")
    print("-" * 64)
    grab, close = _open_camera()
    votes = []
    try:
        for i in range(n):
            frame = grab()
            if frame is None:
                print(f"{i:3d}  프레임 없음")
                continue
            info = HandRecognizer.analyze_opencv(frame)
            g = fingers_to_gesture(info["count"]) if info["count"] is not None else None
            votes.append(g)
            print(f"{i:3d}  {_KO[g]:7s} "
                  f"area={info['area']:7.0f} sol={info['solidity']:.3f} "
                  f"deep={info['deep']}  ({info['reason']})")
            time.sleep(0.08)
    except KeyboardInterrupt:
        print("\n[probe] 중단")
    finally:
        close()

    valid = [v for v in votes if v]
    print("-" * 64)
    if valid:
        tally = Counter(valid)
        win = tally.most_common(1)[0][0]
        print(f"[probe] 다수결 결과: {_KO[win]}   분포={dict(tally)}  "
              f"(유효 {len(valid)}/{len(votes)})")
    else:
        print("[probe] 유효 인식 0 — 손을 카메라에 더 가깝게/조명 밝게 시도")


if __name__ == "__main__":
    main()
