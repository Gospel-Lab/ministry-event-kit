# ministry-event-kit

**교회·비영리 행사의 인쇄물과 신청 페이지를 한 번에 만드는 Claude Code 플러그인.**

행사 정보를 `event.yml` 에 한 번만 적으면 현수막·명찰·신청 페이지가 **실측 인쇄 규격**으로 나옵니다.
행사명이 바뀌어도 한 곳만 고치면 전부 따라 바뀝니다.

```
event.yml  ──┬──▶  현수막      실측 PDF + CMYK 이미지 + 발주안내
             ├──▶  명찰        명단 CSV → 인원수만큼 한 번에 (A4 4개씩 배치본 포함)
             └──▶  신청페이지   구글폼 버튼 + 그대로 배포 가능
```

디자인 도구를 다루지 못해도, 코드를 몰라도 됩니다. 대화로 요청하면 됩니다.

---

## 왜 만들었나

기존 오픈소스 교회 도구(Rock RMS, CiviCRM 등)는 **교인 관리·등록 시스템**입니다.
정작 행사 때 손이 가장 많이 가는 **현수막·명찰·안내 페이지 만들기**는 비어 있습니다.
매번 외주를 맡기거나, 작년 파일을 열어 이름만 고치다 규격이 틀어집니다.

이 키트는 그 빈자리를 채웁니다. 실제 교회 부트캠프에서 쓰며 다듬었습니다.

---

## 설치

Claude Code에서:

```
/plugin marketplace add Gospel-Lab/ministry-event-kit
/plugin install event-kit@ministry-event-kit
```

이미 설치해 두셨다면 **`install` 이 아니라 `update`** 입니다. `install` 은 이미 깔린 플러그인을 그냥 넘어갑니다.

```
/plugin marketplace update ministry-event-kit
/plugin update event-kit@ministry-event-kit
```

설치 없이 시험만 해보려면:

```bash
git clone https://github.com/Gospel-Lab/ministry-event-kit
claude --plugin-dir ./ministry-event-kit
```

### 준비물

| | 필요한 이유 | 없으면 |
|---|---|---|
| **구글 크롬** | 실측 PDF를 만듭니다 | 필수 |
| Python 3.9+ | 생성 스크립트 | 필수 (맥·리눅스는 기본 설치됨) |
| Ghostscript | CMYK 변환 | PDF는 정상, CMYK 이미지만 건너뜁니다 |
| Pillow · numpy | CMYK 색 보정 | 위와 같음 |

```bash
# 맥
brew install ghostscript && pip3 install pillow numpy
# 윈도우
winget install ArtifexSoftware.GhostScript && pip install pillow numpy
```

크롬이 표준 위치에 없으면 `CHROME_PATH` 환경변수로 알려주세요.

**윈도우를 쓰신다면** — 이미 깔려 있는 **엣지(Edge)를 그대로 씁니다.** 크롬을 새로 설치하지 않아도 됩니다. 명령은 `python3` 대신 `python` 또는 `py -3` 입니다.

무엇이 없는지 한 번에 보려면:

```bash
python3 scripts/doctor.py     # 윈도우: python scripts\doctor.py
```

---

## 쓰는 법

```
/event-kit:check      이 컴퓨터에서 돌아가는지 먼저 점검합니다
/event-kit:setup      행사 정보를 물어 event.yml 을 만듭니다
/event-kit:banner     현수막
/event-kit:badge      명찰 (명단 CSV 필요)
/event-kit:landing    신청 랜딩페이지
/event-kit:all        전부 한 번에
```

명령을 외울 필요는 없습니다. **"수련회 현수막 만들어줘"** 라고 하면 Claude가 알아서 씁니다.

### 스크립트로 직접 쓰기

```bash
python3 scripts/make_banner.py  --event event.yml --out out/banner
python3 scripts/make_badges.py  --event event.yml --people participants.csv --out out/badge
python3 scripts/make_landing.py --event event.yml --out out/landing
```

---

## event.yml

`examples/event.yml` 에 전체 항목이 주석과 함께 들어 있습니다. 필요 없는 항목은 지워도 되고, 지우면 안전한 기본값이 쓰입니다.

```yaml
title: 여름 전교인 수련회
organizer: 예시교회
dates: 2026. 8. 3.(월) ~ 8. 5.(수)
place: 가평 수양관

brand:
  palette: plum          # 색 묶음 (아래 표 참고)
  accent: gold           # 강조색만 따로

banner:
  width_mm: 4000         # 400cm
  height_mm: 900         # 90cm
  finish: 봉미싱          # 마감에 따라 글자 여백이 자동으로 달라집니다
  accent_word: 수련회      # 이 단어만 다른 색으로
  show_dates: true       # false 면 날짜를 빼서 다음 해에도 그대로 씁니다
  layout: center         # center / left / split
  motif: circuit         # circuit / grid / dots / plain

schedule:
  - 1일차 8/3 월 | 14:00 등록 · 개회예배
  - 2일차 8/4 화 | 09:30 말씀강의
```

일정은 **`날짜 묶음 | 시간 내용`** 형식으로 씁니다. 이 형식이라야 명찰 뒷면과 랜딩페이지에서 날짜별로 묶입니다.

---

## 우리 단체 색으로 바꾸기

이 키트로 만든 티가 나지 않게, **색과 배치를 갈아끼울 수 있습니다.** 현수막·명찰·랜딩페이지가 늘 함께 바뀝니다.

### 색

세 가지 방법이 있습니다. 아래로 갈수록 자유롭습니다.

```yaml
brand:
  palette: forest              # ① 준비된 색 묶음에서 고르기
```
| | | | |
|---|---|---|---|
| `plum` 보라 | `navy` 남색 | `forest` 녹색 | `wine` 자주 |
| `slate` 청회색 | `clay` 황토 | | |

```yaml
brand:
  palette: navy
  accent: silver               # ② 강조색만 따로 — gold / silver / white / copper 또는 "#e0b96a"
```

강조색은 현수막 제목의 강조 단어, 명찰 참가자 배지와 금색 띠, 랜딩페이지 신청 버튼에 함께 걸립니다.

```yaml
brand:
  colors:
    base:   "#0a2f3a"          # ③ 아무 색이나 직접
    accent: "#e0b96a"
```

`colors` 를 쓰면 명찰 카드 바탕, 랜딩 본문 글자, 구분선까지 **수십 가지 색을 이 두 개에서 계산**합니다. 색을 하나하나 지정할 필요가 없습니다.

바탕색은 **어두운 색**이라야 합니다. 밝은 색을 주면 어둡게 낮추고 알려 드립니다. 현수막이 어두운 바탕에 밝은 글자라는 전제 위에 설계돼 있기 때문입니다.

### 현수막 배치

```yaml
banner:
  layout: left
  motif: dots
```

| `layout` | |
|---|---|
| `center` | 가운데 정렬 — 무대 뒤 배경막처럼 정면에서 보는 자리 (기본) |
| `left` | 왼쪽 정렬 — 오른쪽에 로고나 사진을 붙일 여백이 남습니다 |
| `split` | 좌우 나눔 — 왼쪽에 제목, 오른쪽에 날짜·장소 |

| `motif` | |
|---|---|
| `circuit` | 회로 무늬 (기본) |
| `grid` | 격자만 |
| `dots` | 점무늬 |
| `plain` | 무늬 없음 |

### 색이 안 어울리면 알려줍니다

- 강조색이 바탕색과 같은 색 계열이면 → 강조 단어가 묻힌다고 알립니다
- 강조색이 밝은 무채색(은색·흰색)인데 강조 단어를 지정했으면 → 제목과 구분되지 않는다고 알립니다
- 바탕색이 청보라(색상각 243~264°)면 → 인쇄에서 남색으로 빠진다고 알립니다

멈추지 않고 만들되, 인쇄를 넘기기 전에 볼 수 있게 말해 줍니다.

### 명단 CSV

```csv
이름,소속,역할
김지훈,1교구,참가자
박은혜,청년부,강사
```

구글폼 응답 시트를 CSV로 내려받아 열 이름만 맞추면 그대로 씁니다.

---

## 인쇄 규격 — 이 키트가 대신 챙기는 것

행사 인쇄물에서 사고가 나는 지점은 거의 정해져 있습니다.

- **마감 여백** — 봉미싱은 좌우 15cm가 접힙니다. `finish` 만 정하면 글자 여백이 자동으로 맞춰집니다
- **도련** — 배경을 재단선 밖까지 채웁니다. 안 채우면 가장자리에 흰 줄이 생깁니다
- **글자 크기** — 1m당 3cm 기준. 발주안내에 "몇 미터에서 읽히는지" 계산해 적어줍니다
- **CMYK** — 보라 계열이 남색으로 빠지지 않게 색상각과 잉크 배합을 보정합니다
- **A4 배치** — 명찰을 사무실 프린터로 뽑을 수 있게 2×2로 앉히고 자르는 선을 넣습니다
- **도련 두 가지** — 온라인 주문처는 실측 크기를, 인쇄소는 도련 포함본을 요구합니다. 둘 다 만들어 줍니다
- **해상도 자동 조절** — 5m 백드롭을 150dpi로 만들면 4억 픽셀이라 변환이 멈춥니다. 크기에 맞춰 낮춥니다

### 겪은 함정 (같은 실수를 반복하지 않도록)

1. **Ghostscript `pdfwrite` 의 CMYK 변환을 쓰지 마세요.** 알파가 섞인 방사형 그라데이션이 딱딱한 경계로 깨집니다. RGB로 래스터라이즈한 뒤 ICC 프로파일로 변환해야 매끄럽습니다.
2. **청보라(색상각 252°)는 CMYK에서 남색이 됩니다.** C와 M 값이 비슷해지기 때문입니다. 배경 보라는 275~285°(자보라)로 두고, 변환 후 C에서 M의 18%를 덜어냅니다.
3. **SVG 필터를 쓰지 마세요.** PDF 변환 때 그 요소만 저해상 래스터로 떨어집니다. 입체감은 같은 글자를 겹쳐서 만듭니다.
4. **`<meta name="viewport">` 를 지우지 마세요.** 컴퓨터에서는 멀쩡해 보이는데 휴대폰에서 글자가 잘립니다.
5. **크롬 헤드리스는 창 최소 폭이 500px입니다.** 430px로 캡처하면 500px 화면을 잘라 저장해서 "글자가 잘린다"고 오진하게 됩니다.

---

## 폴더 구조

```
ministry-event-kit/
├─ .claude-plugin/     플러그인·마켓플레이스 매니페스트
├─ skills/             setup · banner · badge · landing · all
├─ scripts/            kit.py(공통 엔진) · theme.py(색) · doctor.py(점검) + 생성기
├─ templates/          현수막 SVG 템플릿
├─ assets/fonts/       Pretendard 서브셋 (OFL 1.1)
├─ examples/           event.yml · participants.csv
└─ docs/               인쇄 규격 참고
```

---

## 기여

행사를 치르며 겪은 것을 나눠주시면 가장 도움이 됩니다.

- 인쇄소에서 반려당한 사례 (규격·색·여백)
- 다른 크기·마감 방식
- 필요한데 없는 산출물 (포스터·X배너·순서지·안내표지 등)

이슈나 PR로 알려주세요. 한국어로 편하게 쓰시면 됩니다.

## 라이선스

- 코드·템플릿: **MIT** ([LICENSE](LICENSE))
- 문서·디자인: **CC BY 4.0**
- 글꼴: **Pretendard** © Kil Hyung-jin — SIL Open Font License 1.1 ([assets/fonts/OFL.txt](assets/fonts/OFL.txt))

예시에 쓰인 교회명·이름·연락처는 모두 가상입니다. 실제 단체명과 로고는 각 단체의 것이니, 만드신 결과물에는 본인 단체의 정보를 넣어 쓰세요.
