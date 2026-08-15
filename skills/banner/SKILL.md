---
description: 행사 현수막을 실측 인쇄 규격으로 만듭니다. 인쇄용 PDF와 CMYK 이미지, 발주 안내문까지 나옵니다. "현수막 만들어줘", "배너 제작", "백드롭" 요청에 사용합니다.
---

# 현수막 만들기

`event.yml` 을 읽어 **인쇄소에 바로 넘길 수 있는** 현수막을 만듭니다.

## 실행

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/make_banner.py" --event event.yml --out out/banner
```

> **윈도우에서는 `python3` 대신 `python` 또는 `py -3` 을 씁니다.**
> 먼저 `python --version` 으로 확인하세요. 아무것도 안 나오면 파이썬이 없는 것이니
> `/event-kit:check` 로 무엇이 없는지 먼저 확인하게 하세요.

`event.yml` 이 없으면 먼저 `/event-kit:setup` 으로 만드세요. 크기·마감·색만 급히 바꾸려면 `event.yml` 의 `banner:` 항목만 고치고 다시 실행하면 됩니다.

## 나오는 것

| 파일 | 쓰임 |
|---|---|
| `banner_print.pdf` | 실측 벡터 PDF — 인쇄소 발주용 |
| `banner_CMYK_(해상도)dpi.jpg` | CMYK 이미지 — 온라인 주문 업로드용. 큰 현수막은 해상도가 자동으로 낮아집니다 |
| `banner.svg` | 편집용 원본 (좌표 1 = 1mm) |
| `발주안내.txt` | 규격·여백·인쇄소에 전달할 문구 |

## 확인하고 알려줄 것

만든 뒤 **결과를 직접 열어보고** 다음을 사용자에게 보고하세요.

1. 실측 크기가 맞는지 — 아래 한 줄이면 윈도우·맥 어디서나 됩니다 (`pdfinfo` 는 윈도우에 없습니다)
   ```bash
   python3 -c "import sys;sys.path.insert(0,r'${CLAUDE_PLUGIN_ROOT}/scripts');from kit import pdf_page_size_mm;from pathlib import Path;print(pdf_page_size_mm(Path('out/banner/banner_print.pdf')))"
   ```
2. 타이틀 글자 높이 — `발주안내.txt` 에 적힌 값. **1m당 3cm** 기준으로 몇 미터에서 읽히는지 함께 말해주세요
3. 파일 용량 — 온라인 주문처는 대개 500MB 이하만 받습니다
4. **`!` 로 시작하는 경고가 떴는지** — 강조색이 바탕과 같은 계열이거나 인쇄에서 색이 빠질 때 알려줍니다. 그냥 넘기지 말고 사용자에게 그대로 전하세요

## 자주 나오는 요청

- **"글씨를 더 크게"** — 글자 크기는 마감 여백 안에서 자동으로 최대치를 씁니다. 더 키우려면 `banner.finish` 를 여백이 작은 마감(`사방미싱`)으로 바꾸거나 제목을 짧게 하세요.
- **"색을 바꿔줘"** — 세 단계로 답하세요.
  1. `brand.palette` — `plum / navy / forest / wine / slate / clay`
  2. `brand.accent` — 강조색만 따로. `gold / silver / white / copper` 또는 `"#e0b96a"`
  3. `brand.colors.base` + `accent` — 단체 상징색이 있으면 이쪽. 나머지 색은 전부 계산됩니다
  셋 다 **명찰·랜딩페이지까지 함께** 바뀝니다. 현수막만 따로 놀지 않습니다.
- **"배치를 바꿔줘"** — `banner.layout` 을 `center / left / split` 중에서 고릅니다.
  오른쪽에 로고나 사진을 붙일 예정이면 `left`, 날짜를 크게 따로 보이려면 `split` 입니다.
- **"배경 무늬가 부담스럽다"** — `banner.motif` 를 `grid`(격자만) 나 `plain`(없음) 으로 바꿉니다.
- **"작년 것을 다시 쓰고 싶다"** — 제목에서 연도를 빼면 다음 해에도 그대로 씁니다. 실무자들이 실제로 쓰는 방법입니다.

## 인쇄 전에 반드시 전할 말

- 배경이 어두우면 **차광(블랙아웃) 원단**을 요청하세요. 보급형은 뒷면이 비칩니다.
- 보라 계열은 CMYK로 인쇄하면 모니터보다 차분하게 나옵니다. 이 키트는 색상각을 미리 보정해 남색으로 빠지는 것은 막아 두었습니다.
