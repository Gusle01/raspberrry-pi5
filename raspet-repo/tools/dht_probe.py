#!/usr/bin/env python3
"""DHT11 배선 진단 도구.

  python3 tools/dht_probe.py [BCM핀번호]   # 기본 19

라인 상태(풀업/전원)와 시작신호 후 센서 응답(커널 엣지 캡처)을 확인한다.
게임 코드와 무관하게 lgpio만 쓰며, 배선/센서 점검용이다.
"""
import sys
import time

import lgpio

PIN = int(sys.argv[1]) if len(sys.argv) > 1 else 19
h = lgpio.gpiochip_open(0)

# 1) 라인에 외부 풀업(=Out핀+전원)이 살아있나: 내부 풀다운을 이기면 살아있음.
lgpio.gpio_claim_input(h, PIN, lgpio.SET_PULL_DOWN)
time.sleep(0.1)
pd = [lgpio.gpio_read(h, PIN) for _ in range(8)]
print(f"[GPIO{PIN}] 내부 풀다운 vs 라인: {pd} → "
      + ("외부 풀업+전원 OK" if sum(pd) > 4 else "풀업 없음(배선/전원 의심)"))
lgpio.gpio_free(h, PIN)

# 2) 시작신호 후 센서 응답(엣지) 캡처.
edges = []
cb = None
ok = 0
for trial in range(5):
    edges.clear()
    lgpio.gpio_claim_output(h, PIN, 0)
    time.sleep(0.020)
    lgpio.gpio_claim_alert(h, PIN, lgpio.BOTH_EDGES)
    cb = lgpio.callback(h, PIN, lgpio.BOTH_EDGES,
                        lambda c, g, level, tick: edges.append((level, tick)))
    time.sleep(0.05)
    cb.cancel()
    lgpio.gpio_free(h, PIN)
    n = len(edges)
    line = f"  시도{trial + 1}: 엣지 {n}개"
    if n >= 2:
        ok += 1
        d = [round((edges[i][1] - edges[i - 1][1]) / 1000.0, 1)
             for i in range(1, min(n, 8))]
        line += f"  앞쪽 간격(µs)={d}"
    print(line)
    time.sleep(1.0)

lgpio.gpiochip_close(h)
print(f"=> 응답 {ok}/5  " + ("(센서 정상 응답!)" if ok else "(무응답 — 배선/센서 점검)"))
