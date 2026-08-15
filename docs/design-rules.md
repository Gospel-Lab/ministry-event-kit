# 행사 성격 → 디자인 규칙

`event.yml` 의 `brief:` 한 덩어리가 색·글자 크기·여백을 바꿉니다.
**감이 아니라 근거로 정했습니다.** 아래 수치의 출처를 함께 적어 둡니다.
바꾸실 때도 근거를 함께 남겨 주세요.

```yaml
brief:
  audience: 장년        # 어린이 / 청소년 / 청년 / 장년 / 어르신 / 전교인 / 외부초청
  mood: 경건            # 경건 / 활기 / 따뜻 / 장중
  formality: 보통       # 격식 / 보통 / 편안
```

세 줄을 적으면 색 묶음·강조색·현수막 배치·글자 크기가 자동으로 정해집니다.
직접 지정한 값(`brand.palette` 등)이 있으면 **그쪽이 항상 이깁니다.** brief 는 비어 있는 자리만 채웁니다.

---

## 대상(audience)

### 어르신 — 이 키트에서 가장 확실한 규칙

나이가 들면 **대비 감도**가 떨어집니다. 40세부터 시작해 80세에는 최대 83% 까지 감소합니다.
글자를 키우는 것보다 **대비를 높이는 것이 먼저**입니다.

| | 값 | 근거 |
|---|---|---|
| 본문 최소 | **12pt** (14~16pt 권장) | ACB 대형인쇄 지침 |
| 행간 | 글자 크기 + 2pt 이상 | 〃 |
| 바탕/글자 | 밝은 바탕에 아주 진한 글자 | 대비 감도 저하 |
| 금지 | 전부 대문자(한글은 전부 굵게), 얇은 획 | 글자 모양 구분이 어려움 |
| 자간·행간 | 넉넉하게 | 〃 |

→ 키트 적용: 글자 배율 **1.15배**, 명찰 뒷면 일정표 글자 확대, 랜딩페이지 본문 17px → 19px

- [Large Print Guidelines — American Council of the Blind](https://www.acb.org/large-print-guidelines)
- [Design Standards for Seniors — Craft & Communicate](https://craftandcommunicate.com/blog/2021/11/08/design-standards-seniors-print-digital-media/)
- [Print and Web Design for Older Adults — Discovery Eye Foundation](https://discoveryeye.org/print-and-web-design-for-older-adults/)

### 어린이

| | 값 |
|---|---|
| 색 비율 | **60-30-10** — 밝은 중립 배경 60% · 밝은 주색 30% · 강조 10% |
| 서체 | 둥근 산세리프 |
| 색 개수 | **2~3개까지** |
| 대상 | 어린이 **와 학부모** 둘 다. 아이에게 신나고 부모에게 믿음직해야 |

→ 키트 적용: 모서리를 둥글게, 숫자를 크게, 강조색을 밝은 쪽으로

> ⚠️ **아직 절반만 됩니다.** 60-30-10 은 밝은 배경을 전제하는데, 이 키트는 현재
> **어두운 배경 + 밝은 글자** 한 장르만 만듭니다(`theme.py` 가 바탕 밝기를 0.14~0.30 으로 제한).
> 어린이 행사에 쓰면 "차분한 어린이 행사물"이 나옵니다. 밝은 테마는 다음 단계 과제입니다.
> **사용자에게 이 한계를 반드시 미리 말하세요.**

- [Kids Color Palette Combinations — Piktochart](https://piktochart.com/blog/kids-color-palette/)

### 청년

대비를 강하게, 사진 자리를 크게. 좌우 나눔(`split`) 배치가 어울립니다.

### 전교인 · 외부초청

가장 넓은 나이대가 봅니다. **어르신 기준을 따르는 것이 안전합니다.**
외부초청은 처음 오는 사람이 보므로 **참여 방법(신청 주소·QR)을 크게** 넣습니다.

---

## 분위기(mood)

| | 색 묶음 | 강조색 | 배경 무늬 |
|---|---|---|---|
| **경건** | navy · plum | gold | grid |
| **활기** | wine · plum | gold | circuit |
| **따뜻** | clay · wine | gold | dots |
| **장중** | navy · slate | silver | plain |

한 가지만 고르는 것이 아니라 **행사 종류와 함께** 봅니다.
예: 부흥회는 활기지만 장년 대상이면 wine 보다 navy 가 낫습니다.

---

## 격식(formality)

| | 여백 | 글자 |
|---|---|---|
| **격식** | 넓게 | 작고 정갈하게, 자간 넓게 |
| **보통** | 기본 | 기본 |
| **편안** | 좁게 | 크고 굵게 |

---

## 포스터 위계 — 대상과 무관하게 공통

Swiss(국제 타이포그래피) 계보의 원칙입니다.

1. **위계는 서체 종류가 아니라 크기 차이로 만든다.** 헤드라인 150pt 대 본문 24pt 처럼 확실하게 벌립니다. 서체를 여러 개 쓰는 것으로는 위계가 안 생깁니다.
2. **서체는 2~3개까지.** 제목용 / 본문용 / (선택) 잔글씨용.
3. **필수 정보 네 가지** — 행사명 · 날짜와 시간 · 장소 · **참여 방법(QR·주소)**. 나머지는 전부 작게.
4. **여백을 아끼지 않는다.** 꽉 채운 포스터는 언제나 진다.
5. **가장 큰 크기로 만들고 줄인다.** 다만 줄이면 작은 글자는 다시 키워야 합니다.

- [Swiss Style / International Typographic Style — TGDS](https://www.thegraphicdesignschool.com/design-history/swiss-style-movement/)
- [Typography Posters — Typography Master](https://www.typographymaster.com/guide/typography-posters)
- [Event Poster Guide — Pixartprinting](https://www.pixartprinting.co.uk/blog/event-poster/)

---

## 규칙보다 사람이 먼저입니다

이 표는 **출발점**이지 정답이 아닙니다.
담당자가 "우리 교회는 초록색"이라고 하면 그 말이 이깁니다. brief 는 아무것도 정해지지 않았을 때
빈칸을 채우기 위한 것입니다.
