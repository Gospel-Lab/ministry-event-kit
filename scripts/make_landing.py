#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
신청 랜딩페이지 만들기 — ministry-event-kit

  python3 scripts/make_landing.py --event examples/event.yml --out out/landing

결과 폴더를 통째로 vercel.com/drop 에 끌어다 놓으면 바로 인터넷 주소가 나옵니다.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import theme  # noqa: E402
from kit import copy_fonts, esc, font_css, info, load_event, ok, warn  # noqa: E402


def build(ev: dict, outdir: Path) -> Path:
    ld = ev.get("landing") or {}
    tk = theme.resolve(ev, warn=warn)
    la = tk["landing"]
    # 강조색(신청 버튼·머리말)은 현수막·명찰과 같은 값을 씁니다
    gold = tk["accent"]["chip"][1]
    ts = tk["brief"]["type_scale"]          # 대상별 본문 글자 배율
    def z(v):                               # 배율이 1이면 값이 그대로 남습니다
        return f"{round(v * ts, 2):g}"
    outdir.mkdir(parents=True, exist_ok=True)
    copy_fonts(outdir)

    title = str(ev.get("title") or "행사")
    headline = str(ld.get("headline") or title)
    lead = str(ld.get("lead") or "")
    cta = str(ld.get("cta_label") or "신청하기")
    form = str(ld.get("form_url") or "#")
    body = ld.get("body") or []
    info_rows = ld.get("info") or []
    sched = ev.get("schedule") or []

    body_html = "\n      ".join(f"<p>{esc(t)}</p>" for t in body)

    rows = []
    for line in info_rows:
        k, _, v = str(line).partition("|")
        rows.append(f'<div class="row"><span class="k">{esc(k.strip())}</span>'
                    f'<span class="v">{esc(v.strip())}</span></div>')
    info_html = "\n        ".join(rows)

    sblocks, cur = [], None
    for line in sched:
        head, _, rest = str(line).partition("|")
        head, rest = head.strip(), rest.strip()
        t, _, what = rest.partition(" ")
        if cur is None or cur[0] != head:
            cur = (head, [])
            sblocks.append(cur)
        cur[1].append((t.strip(), what.strip()))
    sched_html = "\n        ".join(
        f'<div class="day"><h3>{esc(h)}</h3>' +
        "".join(f'<div class="sr"><span class="t">{esc(t)}</span>'
                f'<span class="w">{esc(w)}</span></div>' for t, w in items) + "</div>"
        for h, items in sblocks)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<!-- ★ 이 한 줄이 없으면 휴대폰에서 글자가 잘립니다. 지우지 마세요. -->
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(lead)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(lead)}">
<meta property="og:locale" content="ko_KR">
<style>
  {font_css("")}
  :root {{
    --ink:{la["ink"]}; --deep:{la["deep"]}; --mid:{la["mid"]}; --gold:{gold}; --paper:{la["paper"]};
    --ink2:{la["ink2"]}; --ink3:{la["ink3"]}; --rule:{la["rule"]};
    --hero:{la["hero_text"]}; --hero2:{la["hero_dim"]};
    --sans:"KitSans","Pretendard","Apple SD Gothic Neo","Malgun Gothic",sans-serif;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--paper); color:var(--ink);
    font-family:var(--sans); font-size:{z(17)}px; line-height:1.8;
    -webkit-font-smoothing:antialiased; padding-bottom:86px; }}
  @media (min-width:768px) {{ body {{ padding-bottom:0; }} }}
  .wrap {{ max-width:660px; margin:0 auto; padding:0 22px; }}
  section {{ padding:46px 0; }}
  section + section {{ border-top:1px solid var(--rule); }}
  .kicker {{ font-size:12.5px; font-weight:700; letter-spacing:.16em;
    color:var(--gold); margin-bottom:12px; }}

  header.hero {{ background:linear-gradient(150deg,var(--deep),var(--mid));
    color:#fff; padding:54px 0 58px; position:relative; overflow:hidden; }}
  header.hero::after {{ content:""; position:absolute; inset:auto 0 -40% 0; height:80%;
    background:radial-gradient(ellipse at 50% 0%, rgba(255,255,255,.16), transparent 70%); }}
  .hero .wrap {{ position:relative; }}
  .hero h1 {{ margin:0 0 14px; font-size:clamp(31px,8vw,46px); font-weight:900;
    letter-spacing:-.035em; line-height:1.16; }}
  .hero p {{ margin:0 0 26px; color:var(--hero); font-size:{z(18)}px; max-width:28em; }}
  .hero .when {{ display:inline-flex; flex-wrap:wrap; gap:6px 16px; padding:13px 0;
    border-top:1px solid rgba(255,255,255,.24); border-bottom:1px solid rgba(255,255,255,.24);
    font-variant-numeric:tabular-nums; }}
  .hero .when b {{ font-size:{z(19)}px; font-weight:800; }}
  .hero .when span {{ color:var(--hero2); }}

  .letter p {{ margin:0 0 1.4em; }}
  .letter p:last-child {{ margin-bottom:0; }}

  .info .row {{ display:grid; grid-template-columns:88px minmax(0,1fr); gap:14px;
    padding:13px 0; border-top:1px solid var(--rule); }}
  .info .row:first-of-type {{ border-top:0; }}
  .info .k {{ color:var(--ink3); font-size:{z(14.5)}px; font-weight:700; padding-top:.15em; }}
  .info .v {{ font-variant-numeric:tabular-nums; }}

  .day {{ background:#fff; border:1px solid var(--rule); border-left:4px solid var(--mid);
    border-radius:6px; padding:16px 18px; margin-bottom:12px; }}
  .day h3 {{ margin:0 0 8px; font-size:16px; font-weight:800; color:var(--deep); }}
  .sr {{ display:grid; grid-template-columns:64px minmax(0,1fr); gap:12px;
    padding:5px 0; font-size:{z(16)}px; }}
  .sr .t {{ color:var(--mid); font-weight:700; font-variant-numeric:tabular-nums; }}

  .cta {{ display:flex; align-items:center; justify-content:center; gap:8px; width:100%;
    background:var(--gold); color:{la["ink"]}; font-size:{z(18)}px; font-weight:800;
    text-decoration:none; padding:19px 22px; border-radius:5px;
    transition:filter .12s ease, transform .12s ease; }}
  .cta:hover {{ filter:brightness(1.05); transform:translateY(-1px); }}
  .cta:focus-visible {{ outline:3px solid var(--deep); outline-offset:3px; }}
  @media (prefers-reduced-motion:reduce) {{ .cta {{ transition:none; }} }}
  .apply {{ background:linear-gradient(150deg,var(--deep),var(--mid)); color:#fff; }}
  .apply h2 {{ margin:0 0 10px; font-size:clamp(24px,6vw,32px); font-weight:900;
    letter-spacing:-.03em; }}
  .apply p {{ color:var(--hero); margin:0 0 24px; }}
  .note {{ text-align:center; color:var(--hero2); font-size:13.5px; margin:13px 0 0; }}

  .sticky {{ position:fixed; left:0; right:0; bottom:0; z-index:40;
    background:var(--deep); border-top:1px solid rgba(255,255,255,.16);
    padding:11px 16px calc(11px + env(safe-area-inset-bottom)); }}
  .sticky .cta {{ padding:15px 20px; font-size:16.5px; }}
  @media (min-width:768px) {{ .sticky {{ display:none; }} }}

  footer {{ padding:30px 0 42px; text-align:center; color:var(--ink3);
    font-size:13.5px; border-top:1px solid var(--rule); }}
</style>
</head>
<body>

<header class="hero">
  <div class="wrap">
    <div class="kicker">{esc(ev.get('organizer',''))}</div>
    <h1>{esc(headline)}</h1>
    <p>{esc(lead)}</p>
    <div class="when">
      <b>{esc(ev.get('dates',''))}</b><span>{esc(ev.get('place',''))}</span>
    </div>
  </div>
</header>

<section class="letter">
  <div class="wrap">
      {body_html}
  </div>
</section>

<section class="info">
  <div class="wrap">
    <div class="kicker">안내</div>
        {info_html}
  </div>
</section>

<section>
  <div class="wrap">
    <div class="kicker">일정</div>
        {sched_html}
  </div>
</section>

<section class="apply" id="apply">
  <div class="wrap">
    <h2>{esc(cta)}</h2>
    <p>구글폼으로 이동합니다 · 3분이면 작성됩니다.</p>
    <!-- ★ 구글폼 주소는 event.yml 의 landing.form_url 에서 옵니다. 아래 두 곳이 같아야 합니다. -->
    <a class="cta" href="{esc(form)}" target="_blank" rel="noopener">{esc(cta)} →</a>
    <p class="note">문의 {esc(ev.get('contact',''))}</p>
  </div>
</section>

<footer>{esc(ev.get('organizer',''))} · {esc(title)}</footer>

<div class="sticky">
  <a class="cta" href="{esc(form)}" target="_blank" rel="noopener">{esc(cta)}</a>
</div>

</body>
</html>
"""
    out = outdir / "index.html"
    out.write_text(html, encoding="utf-8")
    ok(f"index.html  ({len(html)//1024}KB · {tk['palette_label']} · {tk['accent_label']} · 의존성 없음)")

    (outdir / "배포안내.txt").write_text(
        f"""랜딩페이지 배포 안내 — {title}

1. 구글폼을 만들고 [보내기] → 링크 → URL 단축 → 복사
2. event.yml 의  landing.form_url  에 붙여넣고 다시 생성
   (또는 index.html 에서 form_url 문자열 두 곳을 직접 교체)
3. vercel.com/drop 에 이 폴더를 통째로 끌어다 놓기
   · 파일 이름은 반드시 index.html 이어야 첫 화면이 뜹니다
   · fonts 폴더를 함께 올려야 글꼴이 유지됩니다
   · 드롭할 때마다 새 주소가 생깁니다. 내용을 다 채운 뒤 마지막에 한 번 올리세요
4. 나온 주소를 휴대폰으로 열어보고 단체 카톡방에 공유

넷리파이를 쓰신다면 app.netlify.com/drop 도 같은 방식입니다.
""", encoding="utf-8")
    ok("배포안내.txt")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="신청 랜딩페이지 생성")
    ap.add_argument("--event", required=True)
    ap.add_argument("--out", default="out/landing")
    a = ap.parse_args()
    ev = load_event(a.event)
    info(f"행사: {ev.get('title')}")
    build(ev, Path(a.out))
    print(f"\n완료 → {Path(a.out).resolve()}")


if __name__ == "__main__":
    main()
