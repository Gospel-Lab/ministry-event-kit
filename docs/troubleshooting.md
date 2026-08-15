# 막혔을 때

## 크롬을 찾지 못합니다

```
크롬을 찾지 못했습니다.
```

구글 크롬을 설치하거나, 이미 있다면 실행 파일 경로를 알려주세요.

```bash
# 맥
export CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# 윈도우 (PowerShell)
$env:CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
```

엣지나 크로미엄도 됩니다. 사파리는 안 됩니다.

## CMYK 변환을 건너뛴다고 나옵니다

```
⚠ Ghostscript가 없어 CMYK 변환을 건너뜁니다 (PDF는 정상 생성됨)
```

**PDF는 정상입니다.** 인쇄소에 PDF만 넘겨도 되고, 온라인 주문처가 CMYK 이미지를 요구할 때만 설치하면 됩니다.

```bash
brew install ghostscript && pip3 install pillow numpy     # 맥
winget install ArtifexSoftware.GhostScript                 # 윈도우
```

## 글자가 잘려 보입니다

- **인쇄물** — 마감 방식(`banner.finish`)이 실제 주문과 다른지 확인하세요. 봉미싱인데 `사방미싱`으로 두면 좌우 12cm가 부족합니다.
- **랜딩페이지** — `index.html` 첫 부분의 `<meta name="viewport">` 줄이 지워졌는지 보세요. 이 줄이 없으면 컴퓨터에서는 멀쩡한데 휴대폰에서 잘립니다.
- **캡처 확인 중이라면** — 크롬 헤드리스는 창 최소 폭이 500px입니다. `--window-size=430`으로 찍으면 500px 화면을 잘라 저장해 "잘렸다"고 오해하게 됩니다. 500 이상으로 찍으세요.

## 명찰에서 이름이 두 줄로 넘어갑니다

이름 글자 수에 따라 크기가 자동으로 줄어듭니다(3자 24 → 4자 18 → 5자 이상 15). 다섯 글자가 넘는 이름이나 영문 이름은 `scripts/make_badges.py` 의 `name_size()` 를 조정하세요.

## 한글이 네모(□)로 보입니다

결과 폴더의 `fonts/` 를 함께 옮기지 않은 경우입니다. **폴더째** 옮기세요. HTML만 따로 빼면 글꼴이 깨집니다.

## 색이 화면과 다릅니다

CMYK 인쇄의 한계입니다. 특히 보라·형광 계열은 모니터보다 차분하게 나옵니다.
이 키트는 남색으로 빠지는 것만 막아 두었습니다. 정확한 색이 필요하면 인쇄소에 **실물 교정**을 요청하세요.

## event.yml 을 못 읽습니다

- 콜론 뒤에 **한 칸 띄기**: `title: 여름 수련회` (`title:여름` ✗)
- 목록은 `- ` 로 시작하고 들여쓰기를 맞춥니다
- 값에 콜론이나 `#` 가 들어가면 따옴표로 감싸세요: `title: "2027: 새로운 시작"`

`pip install pyyaml` 을 하면 더 관대한 파서가 쓰입니다.
