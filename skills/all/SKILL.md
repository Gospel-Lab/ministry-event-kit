---
description: 현수막·명찰·랜딩페이지를 한 번에 만듭니다. 행사 준비를 통째로 맡길 때, "행사 자료 전부 만들어줘", "한 번에 준비해줘" 요청에 사용합니다.
---

# 행사 자료 한 번에 만들기

`event.yml` 하나로 세 가지를 모두 만듭니다.

## 순서

1. `event.yml` 이 있는지 확인합니다. 없으면 `/event-kit:setup` 을 먼저 진행하세요.
2. 명단 CSV가 있는지 확인합니다. 없으면 명찰은 건너뛰고 나머지를 만든 뒤, 명단이 준비되면 `/event-kit:badge` 만 다시 돌리면 된다고 알려주세요.
3. 아래를 차례로 실행합니다.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/make_banner.py"  --event event.yml --out out/banner
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/make_badges.py"  --event event.yml --people participants.csv --out out/badge
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/make_poster.py"  --event event.yml --out out/poster
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/make_landing.py" --event event.yml --out out/landing
```

> **윈도우에서는 `python3` 대신 `python` 또는 `py -3` 을 씁니다.**
> 먼저 `python --version` 으로 확인하세요. 아무것도 안 나오면 파이썬이 없는 것이니
> `/event-kit:check` 로 무엇이 없는지 먼저 확인하게 하세요.

현수막은 CMYK 변환 때문에 **1~2분** 걸립니다. 기다리는 동안 멈춘 것이 아니라고 미리 알려주세요.

## 마치고 보고할 것

만든 파일을 표로 정리해 알려주고, **다음에 사람이 해야 할 일**을 분명히 짚어주세요.

| 만든 것 | 다음에 할 일 |
|---|---|
| 현수막 | 인쇄소 주문 · 차광 원단 요청 |
| 명찰 | A4로 시험 인쇄 후 전량 인쇄 |
| 랜딩페이지 | 구글폼 주소 넣고 vercel.com/drop 에 올리기 |

아직 비어 있는 값(`미정`, 자리표시 구글폼 주소 등)이 있으면 **무엇이 비었는지 목록으로** 알려주세요.
