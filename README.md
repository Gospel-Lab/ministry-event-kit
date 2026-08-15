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

---

## 쓰는 법

```
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
  palette: plum          # plum / navy / forest / wine

banner:
  width_mm: 4000         # 400cm
  height_mm: 900         # 90cm
  finish: 봉미싱          # 마감에 따라 글자 여백이 자동으로 달라집니다
  accent_word: 수련회      # 이 단어만 다른 색으로

schedule:
  - 1일차 8/3 월 | 14:00 등록 · 개회예배
  - 2일차 8/4 화 | 09:30 말씀강의
```

일정은 **`날짜 묶음 | 시간 내용`** 형식으로 씁니다. 이 형식이라야 명찰 뒷면과 랜딩페이지에서 날짜별로 묶입니다.

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
├─ scripts/            kit.py(공통 엔진) + 생성기 3종
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
