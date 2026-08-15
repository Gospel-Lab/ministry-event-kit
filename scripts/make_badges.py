#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
명찰 만들기 — ministry-event-kit

  python3 scripts/make_badges.py --event examples/event.yml \
      --people examples/participants.csv --out out/badge

명단(CSV)을 주면 인원수만큼 한 번에 만듭니다.
  · badges_print.pdf   명찰 한 장이 한 페이지 (인쇄소 발주용)
  · badges_A4.pdf      A4 한 장에 4개 (사무실 프린터용)
  · back_schedule.pdf  뒷면 일정표 (공통 1장)
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import (copy_fonts, esc, font_css, html_to_pdf, info, load_event,  # noqa: E402
                 ok, pdf_to_cmyk_image)

# 색 묶음 — 현수막·랜딩페이지와 같은 이름을 씁니다 (brand.palette)
THEMES = {
    "plum":   dict(deep="#5f34a6", mid="#8a52d2", light="#bb8cec", ink="#2e1348",
                   ink2="#6b5b8a", tint="rgba(123,79,192,", card="#f3ecfc",
                   role="#7b4fc0", role_deep="#6533b0", role_mid="#8f5fd0"),
    "navy":   dict(deep="#1b3a6b", mid="#2f5fa8", light="#7ba3e8", ink="#0f2440",
                   ink2="#4a5d7a", tint="rgba(43,79,140,", card="#e9f0fa",
                   role="#2f5fa8", role_deep="#1b3a6b", role_mid="#3f74c4"),
    "forest": dict(deep="#14513a", mid="#2b8462", light="#6fd4a8", ink="#0d2b20",
                   ink2="#456a5c", tint="rgba(30,110,80,", card="#e7f4ee",
                   role="#2b8462", role_deep="#14513a", role_mid="#37a077"),
    "wine":   dict(deep="#6b1230", mid="#a83057", light="#e08aa4", ink="#2a0714",
                   ink2="#77505f", tint="rgba(150,40,75,", card="#fbeaf0",
                   role="#a83057", role_deep="#6b1230", role_mid="#c04a72"),
}
GOLD = ("linear-gradient(135deg,#ecd69f,#c9a86a)", "#2c1342")


def role_style(role: str, th: dict):
    """참가자는 골드, 강사는 그 행사 색, 나머지는 테두리."""
    if role in ("참가자", "참석자"):
        return GOLD
    if role in ("강사", "강사진", "인도자"):
        return (f"linear-gradient(135deg,{th['role_mid']},{th['role_deep']})", "#ffffff")
    return ("transparent", th["role"])


def css(font_prefix: str, th: dict) -> str:
    return f"""
  {font_css(font_prefix)}
  * {{ box-sizing:border-box; }}
  html,body {{ margin:0; padding:0; }}
  body {{ font-family:"KitSans","Pretendard","Apple SD Gothic Neo",sans-serif;
          -webkit-font-smoothing:antialiased; }}

  .badge {{ position:relative; overflow:hidden; color:#33174f;
    container-type:inline-size;
    background:
      radial-gradient(ellipse 120% 70% at 50% -6%, {th["tint"]}.22), transparent 62%),
      linear-gradient(180deg,{th["card"]} 0%,#faf7fe 55%,#ffffff 100%); }}
  .deco {{ position:absolute; inset:0; z-index:0;
    background-image:
      linear-gradient({th["tint"]}.16) .28cqw, transparent .28cqw),
      linear-gradient(90deg, {th["tint"]}.16) .28cqw, transparent .28cqw);
    background-size:7cqw 7cqw;
    mask-image:
      linear-gradient(180deg,#000 0%,transparent 26%,transparent 74%,#000 100%),
      linear-gradient(90deg,#000 0%,transparent 22%,transparent 78%,#000 100%);
    mask-composite:add; -webkit-mask-composite:source-over; }}
  .corner {{ position:absolute; width:5.4cqw; height:5.4cqw; z-index:3;
    border:.32cqw solid rgba(184,149,91,.62); }}
  .tl {{ top:2cqw; left:2cqw; border-right:0; border-bottom:0; border-top-left-radius:1cqw; }}
  .tr {{ top:2cqw; right:2cqw; border-left:0; border-bottom:0; border-top-right-radius:1cqw; }}
  .bl {{ bottom:2cqw; left:2cqw; border-right:0; border-top:0; border-bottom-left-radius:1cqw; }}
  .br {{ bottom:2cqw; right:2cqw; border-left:0; border-top:0; border-bottom-right-radius:1cqw; }}
  .card {{ position:absolute; inset:4.4cqw; z-index:2; border-radius:3.4cqw;
    overflow:hidden; border:.3cqw solid rgba(184,149,91,.5);
    background:linear-gradient(180deg,#fff 0%,#fbf8fe 62%,{th["card"]} 100%);
    display:flex; flex-direction:column; }}
  .punch {{ position:absolute; top:8.2cqw; left:50%; transform:translateX(-50%);
    width:15cqw; height:3.2cqw; border-radius:2cqw; z-index:8;
    background:rgba(255,255,255,.24); border:.45cqw solid rgba(255,255,255,.45); }}
  .header {{ position:relative; text-align:center; color:#fff;
    background:linear-gradient(132deg,{th["deep"]} 0%,{th["mid"]} 52%,{th["light"]} 100%);
    padding:13.5cqw 5cqw 6cqw;
    border-bottom-left-radius:5cqw; border-bottom-right-radius:5cqw; }}
  .header::after {{ content:""; position:absolute; inset:0;
    background:radial-gradient(ellipse 70% 60% at 22% 0%, rgba(255,255,255,.26), transparent 60%); }}
  .org {{ position:relative; font-size:3.2cqw; font-weight:700; letter-spacing:.13em; color:#f2ddb4; }}
  .ev {{ position:relative; font-size:4.6cqw; font-weight:800; letter-spacing:-.02em; margin-top:1.2cqw; }}
  .gold {{ height:.6cqw; flex:none;
    background:linear-gradient(90deg,transparent,#c9a86a 22%,#eddcb4 50%,#c9a86a 78%,transparent); }}
  .body {{ flex:1; display:flex; flex-direction:column; align-items:center;
    justify-content:center; gap:2.4cqw; padding:3cqw 4.5cqw; text-align:center; }}
  .name {{ font-weight:900; letter-spacing:-.05em; line-height:1; white-space:nowrap; color:{th["ink"]}; }}
  .belong {{ font-size:4cqw; color:{th["ink2"]}; letter-spacing:-.01em; }}
  .role {{ display:inline-block; font-size:3.2cqw; font-weight:800; letter-spacing:.1em;
    padding:1.2cqw 3.8cqw; border-radius:99cqw; margin-top:.4cqw; }}
  .tail {{ flex:none; padding:0 5cqw 4.4cqw; }}
  .band {{ height:1.3cqw; border-radius:99cqw;
    background:linear-gradient(90deg,#c9a86a,#eddcb4 38%,#a97ce0 100%); opacity:.9; }}

  /* 뒷면 일정표 */
  .back {{ padding:1.6cqw 2.2cqw; height:100%; display:flex; flex-direction:column; }}
  .sched {{ flex:1; display:flex; flex-direction:column; gap:.9cqw; }}
  .day {{ background:{th["tint"]}.052); border-radius:2.4cqw; padding:1cqw 1.6cqw; }}
  .dh {{ display:flex; align-items:center; justify-content:space-between;
    gap:1.4cqw; margin-bottom:.6cqw; }}
  .pill {{ display:inline-flex; align-items:baseline; gap:1.2cqw; white-space:nowrap;
    background:linear-gradient(120deg,{th["deep"]},{th["mid"]}); color:#fff;
    border-radius:99cqw; padding:.6cqw 2.2cqw; }}
  .pill b {{ font-size:3.7cqw; font-weight:800; letter-spacing:-.02em; }}
  .r {{ display:grid; grid-template-columns:4.4cqw 11cqw minmax(0,1fr); gap:1.2cqw;
    align-items:center; padding:.15cqw 0; }}
  .no {{ width:4.4cqw; height:4.4cqw; border-radius:50%; background:#fff;
    border:.22cqw solid {th["tint"]}.3); color:{th["deep"]}; font-size:2.75cqw;
    font-weight:800; display:flex; align-items:center; justify-content:center; line-height:1; }}
  .t {{ font-size:3.5cqw; font-weight:700; color:{th["role"]};
    font-variant-numeric:tabular-nums; letter-spacing:-.03em; }}
  .s {{ font-size:3.8cqw; font-weight:600; color:{th["ink"]}; line-height:1.1; letter-spacing:-.03em; }}
  .foot {{ flex:none; margin-top:.9cqw; padding-top:.8cqw; border-top:1px solid #ece3f7;
    font-size:2.9cqw; color:#8d7fae; display:flex; justify-content:space-between; gap:1.4cqw; }}
  .foot b {{ color:{th["ink"]}; }}
"""


def name_size(name: str) -> str:
    n = len([c for c in name if not c.isspace()])
    return {1: "26cqw", 2: "26cqw", 3: "24cqw", 4: "18cqw"}.get(n, "15cqw")


def front_card(ev: dict, person: dict, th: dict) -> str:
    role = (person.get("역할") or person.get("role") or "").strip()
    bg, fg = role_style(role, th)
    border = "" if bg != "transparent" else f"border:.42cqw solid {th['role']};"
    role_html = (f'<span class="role" style="background:{bg};color:{fg};{border}">{esc(role)}</span>'
                 if role else "")
    belong = (person.get("소속") or person.get("belong") or "").strip()
    return f"""<div class="badge">
  <div class="deco"></div>
  <span class="corner tl"></span><span class="corner tr"></span>
  <span class="corner bl"></span><span class="corner br"></span>
  <div class="card">
    <div class="header"><div class="org">{esc(ev.get('organizer',''))}</div>
      <div class="ev">{esc(ev.get('title',''))}</div></div>
    <div class="gold"></div>
    <div class="body">
      <div class="name" style="font-size:{name_size(person.get('이름') or person.get('name') or '')}">{esc(person.get('이름') or person.get('name') or '')}</div>
      {f'<div class="belong">{esc(belong)}</div>' if belong else ''}
      {role_html}
    </div>
    <div class="tail"><div class="band"></div></div>
  </div>
  <div class="punch"></div>
</div>"""


def back_card(ev: dict) -> str:
    """일정표를 '1일차 8/3 월 | 14:00 등록' 형식에서 날짜별로 묶습니다."""
    rows = ev.get("schedule") or []
    groups: list[tuple[str, list[tuple[str, str]]]] = []
    for line in rows:
        head, _, rest = str(line).partition("|")
        head, rest = head.strip(), rest.strip()
        time, _, what = rest.partition(" ")
        if not groups or groups[-1][0] != head:
            groups.append((head, []))
        groups[-1][1].append((time.strip(), what.strip()))

    n = 0
    blocks = []
    for head, items in groups:
        lines = []
        for t, what in items:
            n += 1
            lines.append(f'<div class="r"><span class="no">{n}</span>'
                         f'<span class="t">{esc(t)}</span><span class="s">{esc(what)}</span></div>')
        blocks.append(f'<div class="day"><div class="dh"><span class="pill">'
                      f'<b>{esc(head)}</b></span></div>{"".join(lines)}</div>')

    b = ev.get("badge") or {}
    foot = []
    if b.get("wifi"):
        foot.append(f'<span>와이파이 <b>{esc(b["wifi"])}</b></span>')
    if b.get("desk"):
        foot.append(f'<span><b>{esc(b["desk"])}</b></span>')
    foot_html = f'<div class="foot">{"".join(foot)}</div>' if foot else ""

    return f"""<div class="badge">
  <div class="deco"></div>
  <span class="corner tl"></span><span class="corner tr"></span>
  <span class="corner bl"></span><span class="corner br"></span>
  <div class="card"><div class="back"><div class="sched">{''.join(blocks)}</div>{foot_html}</div></div>
</div>"""


def page_doc(title: str, style_extra: str, cards: list[str], font_prefix: str, th: dict) -> str:
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<title>{esc(title)}</title><style>{css(font_prefix, th)}{style_extra}</style></head>
<body>{''.join(cards)}</body></html>"""


def read_people(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if any((v or "").strip() for v in r.values())]
    if not rows:
        raise SystemExit("명단이 비어 있습니다. 첫 줄은 머리글(이름,소속,역할)이어야 합니다.")
    return rows


def build(ev: dict, people: list[dict], outdir: Path, a4: bool = True) -> None:
    b = ev.get("badge") or {}
    th = THEMES.get(str((ev.get("brand") or {}).get("palette", "plum")), THEMES["plum"])
    w = float(b.get("width_mm", 93))
    h = float(b.get("height_mm", 124))
    outdir.mkdir(parents=True, exist_ok=True)
    copy_fonts(outdir)

    # ① 한 장에 한 명 — 인쇄소 발주용
    one = f"""
  @page {{ size:{w}mm {h}mm; margin:0; }}
  .badge {{ width:{w}mm; height:{h}mm; page-break-after:always; }}
  .badge:last-child {{ page-break-after:auto; }}
"""
    cards = [front_card(ev, p, th) for p in people]
    f1 = outdir / "_front.html"
    f1.write_text(page_doc("명찰 앞면", one, cards, "", th), encoding="utf-8")
    pdf1 = html_to_pdf(f1, outdir / "badges_print.pdf")
    ok(f"badges_print.pdf   {len(people)}명 · 한 장에 한 명 ({w:.0f}×{h:.0f}mm)")

    # ② 뒷면 일정표 (공통 1장)
    f2 = outdir / "_back.html"
    f2.write_text(page_doc("명찰 뒷면", one, [back_card(ev)], "", th), encoding="utf-8")
    html_to_pdf(f2, outdir / "back_schedule.pdf")
    ok("back_schedule.pdf  뒷면 일정표 (공통 1장)")

    # ③ A4 4개씩 — 사무실 프린터용
    if a4:
        per = 4
        pages = []
        for i in range(0, len(cards), per):
            chunk = cards[i:i + per]
            pages.append('<div class="sheet">' + "".join(chunk) + "</div>")
        style = f"""
  @page {{ size:A4; margin:0; }}
  .sheet {{ width:210mm; height:297mm; display:grid;
    grid-template-columns:{w}mm {w}mm; grid-template-rows:{h}mm {h}mm;
    justify-content:center; align-content:center; gap:6mm;
    page-break-after:always; }}
  .sheet:last-child {{ page-break-after:auto; }}
  .badge {{ width:{w}mm; height:{h}mm; outline:.2mm dashed #c9b8e4; outline-offset:0; }}
"""
        f3 = outdir / "_a4.html"
        f3.write_text(page_doc("명찰 A4 배치", style, pages, "", th), encoding="utf-8")
        html_to_pdf(f3, outdir / "badges_A4.pdf")
        sheets = (len(cards) + per - 1) // per
        ok(f"badges_A4.pdf      A4 {sheets}장 (한 장에 4개, 점선은 자르는 선)")

    for tmp in outdir.glob("_*.html"):
        tmp.unlink()

    (outdir / "인쇄안내.txt").write_text(
        f"""명찰 인쇄 안내 — {ev.get('title','')}

완성 규격 : {w:.0f} × {h:.0f} mm (세로형)
인원      : {len(people)}명
용지      : 아트지 200~250g · 무광 코팅 (유광은 조명이 반사돼 이름이 안 보입니다)
색상      : CMYK · 300dpi 권장

파일 쓰임
  badges_print.pdf   인쇄소에 넘길 파일 (한 페이지에 한 명)
  badges_A4.pdf      사무실에서 직접 뽑을 때 (A4 한 장에 4개, 점선을 따라 자르세요)
  back_schedule.pdf  뒷면 일정표 — 양면 인쇄하거나 따로 뽑아 뒤에 넣으세요

역할 배지 색
  참가자 골드 채움 / 강사 보라 채움 / 섬김이·운영 보라 테두리
  명찰은 한 종류로 찍고 배지 색으로만 구분하므로, 남은 명찰은 다음 행사에 그대로 씁니다.
""", encoding="utf-8")
    ok("인쇄안내.txt")


def main() -> None:
    ap = argparse.ArgumentParser(description="명찰 일괄 생성")
    ap.add_argument("--event", required=True)
    ap.add_argument("--people", required=True, help="명단 CSV (이름,소속,역할)")
    ap.add_argument("--out", default="out/badge")
    ap.add_argument("--no-a4", action="store_true", help="A4 배치본을 만들지 않음")
    a = ap.parse_args()
    ev = load_event(a.event)
    people = read_people(Path(a.people))
    info(f"행사: {ev.get('title')} · 명단 {len(people)}명")
    build(ev, people, Path(a.out), a4=not a.no_a4)
    print(f"\n완료 → {Path(a.out).resolve()}")


if __name__ == "__main__":
    main()
