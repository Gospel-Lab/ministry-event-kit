#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
포스터 만들기 — ministry-event-kit

  python3 scripts/make_poster.py --event event.yml --out out/poster

인쇄용(A3·A2·A1)과 카톡·인스타에 올릴 웹포스터를 함께 만듭니다.

설계 원칙 (docs/design-rules.md)
  · 위계는 서체 종류가 아니라 크기 차이로 만든다
  · 필수 정보 네 가지 — 행사명 / 날짜·시간 / 장소 / 참여 방법
  · 여백을 아끼지 않는다
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import theme  # noqa: E402
from kit import (copy_fonts, esc, font_css, html_to_pdf, html_to_png, info,  # noqa: E402
                 load_event, ok, pdf_to_cmyk_image, warn)

# 이름: (가로mm, 세로mm, 1장 인쇄비 안내)
SIZES = {
    "A4": (210, 297, "500~1,500원"),
    "A3": (297, 420, "1,000~3,000원"),
    "A2": (420, 594, "2,000~5,000원"),
    "A1": (594, 841, "5,000~10,000원"),
}
# 게시판·복도에 가장 많이 붙는 크기입니다
DEFAULT_SIZE = "A3"

WEB = {"web_square.png": (1080, 1080), "web_story.png": (1080, 1920)}


def make_qr(text: str, dark: str, out: Path) -> Path | None:
    """QR 이미지를 SVG로 만듭니다. 라이브러리가 없으면 만들지 않습니다.

    없어도 포스터는 나옵니다 — 대신 주소를 글자로 넣습니다.
    """
    if not text or not text.startswith(("http://", "https://")):
        return None
    try:
        import segno
        segno.make(text, error="m").save(str(out), scale=10, dark=dark, light=None)
        return out
    except ImportError:
        pass
    try:
        import qrcode
        import qrcode.image.svg as qsvg
        img = qrcode.make(text, image_factory=qsvg.SvgPathImage, box_size=10, border=2)
        img.save(str(out))
        return out
    except ImportError:
        return None


def build(ev: dict, outdir: Path) -> None:
    po = ev.get("poster") or {}
    outdir.mkdir(parents=True, exist_ok=True)
    copy_fonts(outdir)

    tk = theme.resolve(ev, warn=warn)
    bn, la, acc, bf = tk["banner"], tk["landing"], tk["accent"], tk["brief"]

    size_name = str(po.get("size", DEFAULT_SIZE)).upper().strip()
    if size_name not in SIZES:
        if size_name:
            warn(f"'{size_name}' 은 없는 규격입니다. 쓸 수 있는 값: "
                 f"{' / '.join(SIZES)} → {DEFAULT_SIZE} 로 진행합니다.")
        size_name = DEFAULT_SIZE
    w, h, price = SIZES[size_name]
    bleed = float(po.get("bleed_mm", 3))

    title = str(ev.get("title") or "행사 이름")
    org = str(ev.get("organizer") or "")
    dates = str(ev.get("dates") or "").strip()
    place = str(ev.get("place") or "").strip()
    contact = str(ev.get("contact") or "").strip()
    lead = str(po.get("lead") or (ev.get("landing") or {}).get("lead") or "").strip()
    join_url = str(po.get("join_url") or
                   (ev.get("landing") or {}).get("form_url") or "").strip()
    join_label = str(po.get("join_label") or "신청하기").strip()
    accent_word = str(po.get("accent_word") or
                      (ev.get("banner") or {}).get("accent_word") or "").strip()

    if accent_word and title.endswith(accent_word):
        head, tail = title[: -len(accent_word)], accent_word
    else:
        head, tail = title, ""

    # ── 위계: 크기 차이로 만듭니다 ──
    # 기준 폭을 100 으로 놓고 비율로 적습니다. 어느 규격에서도 같은 비율이 나옵니다.
    # 대상이 어르신이면 잔글씨를 키우고 제목을 조금 줄여 균형을 맞춥니다.
    ts = bf["type_scale"]
    space = bf["space"]
    t_size = 13.5 / (1 + (ts - 1) * 0.7)      # 제목
    small = 3.0 * ts                           # 잔글씨
    body = 3.9 * ts                            # 본문
    big = 5.4 * ts                             # 날짜·장소
    pad = round(7.5 * space, 2)

    # 제목이 길면 줄입니다 (한 줄에 들어갈 글자 수 기준)
    em = sum(0.62 if c.isascii() else 1.0 for c in title)
    if em > 9:
        t_size *= 9 / em
    t_size = round(t_size, 2)

    qr_path = make_qr(join_url, la["ink"], outdir / "qr.svg")
    if join_url and not qr_path:
        info("QR 라이브러리가 없어 주소를 글자로 넣습니다 "
             "(pip3 install segno 로 설치하면 QR 이 들어갑니다)")

    schedule = ev.get("schedule") or []
    sched_rows = []
    seen = set()
    for line in schedule:
        head_s, _, rest = str(line).partition("|")
        head_s = head_s.strip()
        if head_s in seen:
            continue
        seen.add(head_s)
        t, _, what = rest.strip().partition(" ")
        sched_rows.append((head_s, f"{t.strip()} {what.strip()}".strip()))
    sched_html = "".join(
        f'<div class="srow"><span class="sd">{esc(d)}</span>'
        f'<span class="sw">{esc(x)}</span></div>' for d, x in sched_rows[:4])

    info_bits = []
    if dates:
        info_bits.append(("날짜", dates))
    if place:
        info_bits.append(("장소", place))
    for row in (po.get("info") or []):
        k, _, v = str(row).partition("|")
        info_bits.append((k.strip(), v.strip()))

    join_html = ""
    if join_url and qr_path:
        join_html = (f'<div class="join"><img class="qr" src="qr.svg" alt="">'
                     f'<div class="jt"><b>{esc(join_label)}</b>'
                     f'<span>휴대폰 카메라로 비추세요</span></div></div>')
    elif join_url:
        # QR 을 못 만들었을 때 — 주소를 크게 글자로 넣습니다
        short = join_url.replace("https://", "").replace("http://", "")
        join_html = (f'<div class="join joint"><div class="jt"><b>{esc(join_label)}</b>'
                     f'<span class="url">{esc(short)}</span></div></div>')

    css = f"""
  {font_css("")}
  * {{ box-sizing:border-box; }}
  html,body {{ margin:0; padding:0; }}
  @page {{ size:{w}mm {h}mm; margin:0; }}
  body {{ font-family:"KitSans","Pretendard","Apple SD Gothic Neo",sans-serif;
    -webkit-font-smoothing:antialiased;
    /* 한글은 이것이 없으면 "여름 전교 / 인 수련회" 처럼 단어 중간에서 끊깁니다 */
    word-break:keep-all; }}

  .sheet {{ width:{w}mm; height:{h}mm; position:relative; overflow:hidden;
    container-type:inline-size; display:flex; flex-direction:column;
    color:#fff;
    background:
      radial-gradient(ellipse 90% 45% at 50% 6%, rgba(255,255,255,.10), transparent 62%),
      linear-gradient(168deg,{bn["bg"][0]} 0%,{bn["bg"][1]} 34%,{bn["bg"][2]} 68%,{bn["bg"][3]} 100%); }}
  .grid {{ position:absolute; inset:0; z-index:0; opacity:.5;
    background-image:
      linear-gradient({bn["grid"]}22 .18cqw, transparent .18cqw),
      linear-gradient(90deg,{bn["grid"]}22 .18cqw, transparent .18cqw);
    background-size:11cqw 11cqw;
    mask-image:linear-gradient(180deg,#000,transparent 42%,transparent 62%,#000); }}
  .in {{ position:relative; z-index:1; padding:{pad}cqw; height:100%;
    display:flex; flex-direction:column; }}

  .top {{ flex:none; display:flex; align-items:center; gap:2.4cqw; }}
  .top .bar {{ width:{round(4.5*space,2)}cqw; height:.42cqw; background:{acc["acc"][1]}; }}
  .org {{ font-size:{round(small,2)}cqw; font-weight:700; letter-spacing:.16em;
    color:{acc["org"]}; }}

  .mid {{ flex:1; display:flex; flex-direction:column; justify-content:center;
    gap:{round(2.6*space,2)}cqw; padding:{round(3*space,2)}cqw 0; }}
  h1 {{ margin:0; font-size:{t_size}cqw; font-weight:900; letter-spacing:-.045em;
    line-height:1.06; text-wrap:balance; word-break:keep-all;
    background:linear-gradient(180deg,#fff 0%,{bn["hi"][1]} 38%,{bn["hi"][2]} 100%);
    -webkit-background-clip:text; background-clip:text; color:transparent; }}
  h1 .acc {{ background:linear-gradient(180deg,{acc["acc"][0]},{acc["acc"][1]} 52%,{acc["acc"][2]});
    -webkit-background-clip:text; background-clip:text; color:transparent; }}
  .lead {{ margin:0; font-size:{round(body,2)}cqw; font-weight:500; line-height:1.55;
    color:{bn["sub"]}; max-width:26em; }}

  .when {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:1.2cqw 3cqw;
    padding:{round(2.2*space,2)}cqw 0; border-top:.12cqw solid {acc["acc"][1]}55;
    border-bottom:.12cqw solid {acc["acc"][1]}55;
    font-variant-numeric:tabular-nums; }}
  .when b {{ font-size:{round(big,2)}cqw; font-weight:800; letter-spacing:-.02em;
    color:{acc["acc"][0]}; }}
  .when span {{ font-size:{round(body,2)}cqw; font-weight:600; color:#fff; }}

  .srow {{ display:grid; grid-template-columns:minmax(0,10em) minmax(0,1fr);
    gap:2cqw; padding:.55cqw 0; font-size:{round(small*1.12,2)}cqw; color:{bn["sub"]}; }}
  .srow .sd {{ font-weight:800; color:{acc["acc"][1]}; }}

  .bot {{ flex:none; display:flex; align-items:flex-end; justify-content:space-between;
    gap:3cqw; }}
  .facts {{ flex:1 1 auto; min-width:0; display:flex; flex-direction:column; gap:.8cqw; }}
  .fact {{ display:grid; grid-template-columns:minmax(0,5em) minmax(0,1fr); gap:1.6cqw;
    font-size:{round(small*1.12,2)}cqw; }}
  .fact .k {{ font-weight:700; color:{acc["acc"][1]}; letter-spacing:.06em; }}
  .fact .v {{ color:#fff; font-weight:600; min-width:0; overflow-wrap:anywhere; }}

  .join {{ flex:0 0 auto; margin-left:auto; display:flex; align-items:center; gap:1.8cqw;
    background:#fff; border-radius:1.4cqw; padding:1.5cqw 2cqw; color:{la["ink"]}; }}
  .join .qr {{ width:{round(13*space,2)}cqw; height:{round(13*space,2)}cqw; display:block; }}
  .join .jt {{ display:flex; flex-direction:column; gap:.35cqw; }}
  .join .jt b {{ font-size:{round(body,2)}cqw; font-weight:900; letter-spacing:-.02em; }}
  .join .jt span {{ font-size:{round(small*.92,2)}cqw; color:{la["ink2"]}; }}
  .joint {{ max-width:52%; }}
  .joint .url {{ font-size:{round(small*1.05,2)}cqw; font-weight:700;
    color:{la["deep"]}; word-break:break-all; }}

  .foot {{ flex:none; margin-top:{round(2.2*space,2)}cqw;
    font-size:{round(small*.92,2)}cqw; color:{bn["sub"]}; opacity:.9; }}
"""

    sheet = f"""<div class="sheet">
  <div class="grid"></div>
  <div class="in">
    <div class="top"><span class="bar"></span><span class="org">{esc(org)}</span></div>
    <div class="mid">
      <h1>{esc(head)}<span class="acc">{esc(tail)}</span></h1>
      {f'<p class="lead">{esc(lead)}</p>' if lead else ''}
      <div class="when">
        {f'<b>{esc(dates)}</b>' if dates else ''}
        {f'<span>{esc(place)}</span>' if place else ''}
      </div>
      {f'<div class="sched">{sched_html}</div>' if sched_html else ''}
    </div>
    <div class="bot">
      <div class="facts">
        {''.join(f'<div class="fact"><span class="k">{esc(k)}</span><span class="v">{esc(v)}</span></div>' for k, v in info_bits[2:])}
      </div>
      {join_html}
    </div>
    <div class="foot">{esc(org)}{f' · 문의 {esc(contact)}' if contact else ''}</div>
  </div>
</div>"""

    doc = (f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">'
           f'<title>{esc(title)} 포스터</title><style>{css}</style></head>'
           f'<body>{sheet}</body></html>')
    src = outdir / "_poster.html"
    src.write_text(doc, encoding="utf-8")

    pdf = html_to_pdf(src, outdir / f"poster_{size_name}.pdf")
    ok(f"인쇄용 PDF  {pdf.name}  ({w} × {h} mm · {size_name})")

    # 도련 포함본 — 배경을 재단선 밖까지 늘립니다
    fw, fh = w + bleed * 2, h + bleed * 2
    doc_b = doc.replace(f"@page {{ size:{w}mm {h}mm; margin:0; }}",
                        f"@page {{ size:{fw}mm {fh}mm; margin:0; }}") \
               .replace(f".sheet {{ width:{w}mm; height:{h}mm;",
                        f".sheet {{ width:{fw}mm; height:{fh}mm;") \
               .replace(f'.in {{ position:relative; z-index:1; padding:{pad}cqw;',
                        f'.in {{ position:relative; z-index:1; '
                        f'padding:calc({pad}cqw + {bleed}mm);')
    srcb = outdir / "_poster_bleed.html"
    srcb.write_text(doc_b, encoding="utf-8")
    pdfb = html_to_pdf(srcb, outdir / f"poster_{size_name}_bleed.pdf")
    ok(f"도련 포함본 {pdfb.name}  ({fw:.0f} × {fh:.0f} mm)")

    jpg = pdf_to_cmyk_image(pdf, outdir / f"poster_{size_name}_CMYK_300dpi.jpg", dpi=300)
    if jpg:
        ok(f"CMYK 이미지 {jpg.name}  ({jpg.stat().st_size/1048576:.1f} MB, 300dpi)")

    # ── 웹포스터 — 카톡·인스타용 ──
    for name, (pw, ph) in WEB.items():
        wdoc = doc.replace(f"@page {{ size:{w}mm {h}mm; margin:0; }}", "") \
                  .replace(f".sheet {{ width:{w}mm; height:{h}mm;",
                           f".sheet {{ width:{pw}px; height:{ph}px;")
        if ph > pw:
            # 세로형(스토리)은 인스타·카톡의 화면 단추가 위아래를 덮습니다.
            # 위 10% · 아래 15% 를 비워 두어야 신청 버튼이 가려지지 않습니다.
            wdoc = wdoc.replace(f".in {{ position:relative; z-index:1; padding:{pad}cqw;",
                                f".in {{ position:relative; z-index:1; "
                                f"padding:{round(ph*0.10)}px {pad}cqw {round(ph*0.15)}px;")
        wsrc = outdir / f"_{name}.html"
        wsrc.write_text(wdoc, encoding="utf-8")
        html_to_png(wsrc, outdir / name, pw, ph)
        ok(f"웹포스터   {name}  ({pw}×{ph})")
        wsrc.unlink(missing_ok=True)

    src.unlink(missing_ok=True)
    srcb.unlink(missing_ok=True)

    qr_note = ("QR 코드   : 들어갔습니다. 인쇄 후 실제 휴대폰으로 반드시 한 번 찍어보세요"
               if qr_path else
               "QR 코드   : 없습니다 (주소를 글자로 넣었습니다). "
               "pip3 install segno 후 다시 만들면 QR 이 들어갑니다"
               if join_url else
               "QR 코드   : 신청 주소가 없어 넣지 않았습니다")
    brief_note = (f"\n대상      : {bf['audience']} — 글자를 {ts:.0%} 로 맞췄습니다"
                  if bf["audience"] else "")

    (outdir / "인쇄안내.txt").write_text(
        f"""포스터 인쇄 안내 — {title}

규격      : {size_name} ({w} × {h} mm) · 1장 인쇄비 대략 {price}
용지      : 스노우지 200~250g (무광). 실내 게시용
색상      : CMYK · 300dpi{brief_note}
{qr_note}

파일 쓰임
  poster_{size_name}.pdf        실측 크기 · 도련 없음 — 온라인 주문처
  poster_{size_name}_bleed.pdf  사방 {bleed:.0f}mm 도련 포함 — 인쇄소
  poster_{size_name}_CMYK_300dpi.jpg  이미지 업로드용
  web_square.png                카톡·인스타 피드 (1080×1080)
  web_story.png                 인스타·카톡 스토리 (1080×1920)

붙이기 전에 확인할 것
  · 세 걸음 떨어져서 행사명이 읽히는지
  · 날짜와 장소가 한눈에 들어오는지
  · 신청 방법이 보이는지 — 이게 없으면 포스터가 일을 안 합니다
""", encoding="utf-8")
    ok("인쇄안내.txt")


def main() -> None:
    ap = argparse.ArgumentParser(description="포스터 생성")
    ap.add_argument("--event", required=True)
    ap.add_argument("--out", default="out/poster")
    ap.add_argument("--size", help="A4 / A3 / A2 / A1 (없으면 event.yml 또는 A3)")
    a = ap.parse_args()
    ev = load_event(a.event)
    if a.size:
        ev.setdefault("poster", {})["size"] = a.size
    info(f"행사: {ev.get('title')}")
    build(ev, Path(a.out))
    print(f"\n완료 → {Path(a.out).resolve()}")


if __name__ == "__main__":
    main()
