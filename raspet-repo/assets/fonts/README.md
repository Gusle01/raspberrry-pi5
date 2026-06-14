# 번들 폰트 — Galmuri (픽셀 한글 폰트)

작은 OLED(128×64)에서 한글이 또렷하게 보이도록 픽셀(비트맵) 폰트를 번들한다.
아웃라인 폰트(Noto/Un 등)는 8~11px에서 획이 뭉개지지만, Galmuri는 작은 크기 전용으로
디자인되어 선명하다.

| 파일 | 용도 | 권장 크기 |
|---|---|---|
| `Galmuri7.ttf`  | 작은 목록(`FONT_SIZE_SMALL`) | 7·14px |
| `Galmuri11.ttf` | 본문·강조(`FONT_SIZE`, `FONT_SIZE_BIG`) | 11·22px |

- **폰트:** Galmuri — © 2019–2025 Lee Minseo (quiple), v2.40.3
- **라이선스:** SIL Open Font License 1.1 (`OFL.txt` 참조). 예약 폰트 이름(RFN) 없음.
- **원본:** https://github.com/quiple/galmuri
- **연결:** `src/raspet/config.py`의 `FONT_FILE*`가 이 파일들을 가리킨다.
  파일이 없으면 `FONT_CANDIDATES` 자동 탐색(시스템 한글 폰트)으로 폴백한다.

## 서브셋 (용량 축소)

원본은 한자·가나까지 포함해 파일당 ~4–5MB다. 게임에 필요한 글자(ASCII + 한글 전체 +
UI 기호)만 남겨 서브셋했다. 재현:

```bash
pip install fonttools
RANGES="U+0020-007E,U+00A0-00FF,U+1100-11FF,U+3130-318F,U+AC00-D7A3,U+2010-2027,U+2500-26FF,U+2700-27BF"
pyftsubset Galmuri7.ttf  --unicodes="$RANGES" --layout-features='*' --output-file=Galmuri7.ttf
pyftsubset Galmuri11.ttf --unicodes="$RANGES" --layout-features='*' --output-file=Galmuri11.ttf
```

> UI 기호 중 ✔(U+2714)는 Galmuri에 없어, 업적 표시는 폰트에 있는 ★/☆를 쓴다.
