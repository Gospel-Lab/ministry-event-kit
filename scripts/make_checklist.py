#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
준비 체크리스트 만들기 — ministry-event-kit

  python3 scripts/make_checklist.py --event event.yml --out out/checklist

행사 준비물·할 일을 A4 한 장짜리 체크리스트 PDF 로 만듭니다.
총무가 출력해서 펜으로 지워 가며 쓰는 용도입니다.

event.yml 에 checklist 가 없으면 행사 준비의 기본 항목(D-30 ~ 당일)으로 채웁니다.

  checklist:
    title: 준비 체크리스트 (총무 확인용)
    facts:                       # 위쪽 요약 상자 — 머리 | 내용
      - 버스 | 충북70바0000 · 기사님 010-0000-0000
    todo:                        # 묶음 | 할 일 | 담당(선택)
      - 순서지 수정 | 장소명 **막동사랑교회**로 고치기
      - 연락 | 식당 인원 30명 재확인 | 회계

  · 같은 묶음 이름은 처음 나온 순서대로 한 칸에 모입니다
  · **굵게** 로 감싼 글자는 굵게 나옵니다
  · 한 장을 넘으면 글자를 조금씩 줄여 한 장에 맞춥니다
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import theme  # noqa: E402
from kit import (copy_fonts, esc, font_css, html_to_pdf, info, load_event,  # noqa: E402
                 ok, warn)

# 행사 준비의 기본 순서. checklist.todo 를 적지 않았을 때 씁니다.
DEFAULT_TODO = [
    "D-30 기획 | 날짜·장소·예산 확정",
    "D-30 기획 | 회비·후원 계좌 정하기",
    "D-30 기획 | 신청 안내 올리기 (포스터·신청 페이지)",
    "D-14 예약 | 신청 마감 · 참가자 명단 정리",
    "D-14 예약 | 차량 · 식당 · 숙소 예약",
    "D-14 예약 | 현수막 인쇄 주문",
    "D-14 예약 | 후원·협조 공문 발송",
    "D-3 점검 | 최종 인원 확정 → 식당·차량·방문처에 알리기",
    "D-3 점검 | 회비·후원금 입금 확인",
    "D-3 점검 | 순서지 · 명찰 · 출석부 출력",
    "D-3 점검 | 간식 · 물 · 선물 · 비상 상비약",
    "D-3 점검 | 참가자 단톡방 공지 (집결 시간·장소·준비물)",
    "당일 가져갈 것 | 출석부 · 볼펜",
    "당일 가져갈 것 | 순서지 · 명찰",
    "당일 가져갈 것 | 현수막 · 케이블타이 · 집게",
    "당일 가져갈 것 | 현장 수금 명단 · 거스름돈",
    "당일 가져갈 것 | 휴대폰 충전 · 보조배터리 (사진 담당)",
]

# 한 장에 안 들어가면 이 순서로 글자를 줄여 봅니다
SCALES = (1.0, 0.92, 0.85, 0.78)


def rows_of(items) -> list[list[str]]:
    out = []
    for it in items or []:
        # "- 기도자: 설재길" 처럼 콜론 뒤에 공백이 있으면 YAML 이 사전으로 읽습니다.
        # 사용자는 그냥 문장을 적은 것이므로 원래 글자로 되돌립니다.
        if isinstance(it, dict):
            it = ", ".join(f"{k}: {v}" for k, v in it.items())
        parts = [p.strip() for p in str(it).split("|")]
        if any(parts):
            out.append(parts)
    return out


def rich(s: str) -> str:
    """**굵게** 만 지원합니다. 나머지는 그대로 이스케이프합니다."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(s))


def group_todo(rows: list[list[str]]) -> list[tuple[str, list[tuple[str, str]]]]:
    groups: dict[str, list[tuple[str, str]]] = {}
    for parts in rows:
        if len(parts) == 1:                        # 묶음 없이 할 일만 적은 줄
            head, task, who = "할 일", parts[0], ""
        else:
            head, task = parts[0] or "할 일", parts[1]
            who = parts[2] if len(parts) > 2 else ""
        if task:
            groups.setdefault(head, []).append((task, who))
    return list(groups.items())


def page_count(pdf: Path) -> int:
    raw = pdf.read_bytes()
    counts = [int(n) for n in re.findall(rb"/Type\s*/Pages\b[^>]*?/Count\s+(\d+)", raw)]
    if counts:
        return max(counts)
    return len(re.findall(rb"/Type\s*/Page\b(?!s)", raw)) or 1


def render(ev: dict, scale: float) -> str:
    cl = ev.get("checklist") or {}
    if not isinstance(cl, dict):
        cl = {}
    tk = theme.resolve(ev)
    la, acc = tk["landing"], tk["accent"]

    title = str(ev.get("title") or "행사")
    org = str(ev.get("organizer") or "")
    dates = str(ev.get("dates") or "").strip()
    place = str(ev.get("place") or "").strip()
    contact = str(ev.get("contact") or "").strip()
    sub = str(cl.get("title") or "준비 체크리스트").strip()

    # ── 요약 상자 ──
    facts = rows_of(cl.get("facts"))
    if not facts:
        if dates:
            facts.append(["날짜", dates])
        if place:
            facts.append(["장소", place])
        # 여러 날 행사면 날이 바뀌는 곳에만 "1일차 8/3 월" 같은 머리를 붙입니다
        sched, last = [], None
        for s in ev.get("schedule") or []:
            head, _, rest = str(s).partition("|")
            head, rest = head.strip(), rest.strip()
            if not rest:
                sched.append(head)
                continue
            sched.append(f"[{head}] {rest}" if head != last else rest)
            last = head
        if sched:
            facts.append(["일정", " → ".join(sched[:8])])
        if contact and contact != "미정":
            facts.append(["문의", contact])
    facts_html = "".join(
        f'<div class="f"><b>{esc(p[0])}</b><span>{rich(" | ".join(p[1:]))}</span></div>'
        for p in facts if len(p) > 1)

    # ── 할 일 ──
    todo = rows_of(cl.get("todo")) or rows_of(DEFAULT_TODO)
    groups = group_todo(todo)
    sec = []
    for head, items in groups:
        lis = "".join(
            f'<li>{rich(task)}{f"<span class=who>{esc(who)}</span>" if who else ""}</li>'
            for task, who in items)
        sec.append(f'<section><h2>{rich(head)}</h2><ul>{lis}</ul></section>')

    # 할 일이 짧으면 두 칸으로 나눠 한 장에 더 많이 담습니다
    lens = [len(t) + len(w) for _, its in groups for t, w in its]
    two_col = bool(lens) and sum(lens) / len(lens) <= 30

    fs = round(9.8 * scale, 2)
    meta = " · ".join(x for x in (org, dates) if x)

    css = f"""
  {font_css("")}
  @page {{ size: A4; margin: 11mm 13mm 10mm; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ height: 100%; }}
  body {{ font-family: "KitSans", "Pretendard", "Malgun Gothic", "Apple SD Gothic Neo", sans-serif;
    color: {la["ink"]}; font-size: {fs}pt; line-height: 1.4; word-break: keep-all;
    -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  .sheet {{ min-height: 275mm; display: flex; flex-direction: column; }}
  header {{ display: flex; justify-content: space-between; align-items: flex-end; gap: 4mm;
    border-bottom: 2.5px solid {la["deep"]}; padding-bottom: 1.6mm; margin-bottom: 2.6mm; }}
  h1 {{ font-size: {round(fs * 1.8, 2)}pt; font-weight: 900; letter-spacing: -.03em; color: {la["deep"]}; }}
  h1 small {{ font-size: {round(fs * 1.02, 2)}pt; font-weight: 600; color: {la["ink2"]};
    margin-left: 2mm; letter-spacing: 0; }}
  .meta {{ text-align: right; font-size: {round(fs * .86, 2)}pt; color: {la["ink2"]}; }}
  .facts {{ background: {la["paper"]}; border: 1px solid {la["rule"]}; border-radius: 1.2mm;
    padding: 1.6mm 3mm; margin-bottom: 2.6mm; font-size: {round(fs * .9, 2)}pt; }}
  .f {{ display: grid; grid-template-columns: 9mm 1fr; gap: 2mm; padding: .3mm 0; }}
  .f b {{ color: {la["deep"]}; font-weight: 800; }}
  .todo {{ {"columns: 2; column-gap: 4mm;" if two_col else ""} }}
  section {{ break-inside: avoid; margin-bottom: 2.4mm; }}
  h2 {{ font-size: {round(fs * 1.06, 2)}pt; font-weight: 800; color: #fff; background: {la["deep"]};
    padding: .6mm 2.6mm; border-radius: .8mm; }}
  ul {{ list-style: none; }}
  li {{ position: relative; padding: .9mm 1mm .9mm 5.4mm; border-bottom: 1px dotted {la["rule"]}; }}
  li::before {{ content: ""; position: absolute; left: 1mm; top: 1.55mm; width: 3mm; height: 3mm;
    border: 1.3px solid {la["ink"]}; border-radius: .5mm; }}
  li b {{ color: {la["deep"]}; }}
  .who {{ float: right; padding-left: 2mm; font-size: {round(fs * .84, 2)}pt; color: {la["ink3"]};
    white-space: nowrap; }}
  .memo {{ flex: 1; min-height: 14mm; margin-top: 1mm; border: 1px solid {la["rule"]};
    border-radius: 1.2mm; padding: 1mm 2.4mm; font-size: {round(fs * .86, 2)}pt; color: {la["ink3"]}; }}
  .bar {{ height: 1.2mm; background: {acc["acc"][1]}; margin-top: 2mm; border-radius: .6mm; }}
"""
    return (f'<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">'
            f'<title>{esc(title)} 체크리스트</title><style>{css}</style></head><body>'
            f'<div class="sheet">'
            f'<header><h1>{esc(title)}<small>{esc(sub)}</small></h1>'
            f'<div class="meta">{esc(meta)}</div></header>'
            f'{f"<div class=facts>{facts_html}</div>" if facts_html else ""}'
            f'<div class="todo">{"".join(sec)}</div>'
            f'<div class="memo">메모</div><div class="bar"></div>'
            f'</div></body></html>')


def build(ev: dict, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    copy_fonts(outdir)
    cl = ev.get("checklist")
    if not (isinstance(cl, dict) and cl.get("todo")):
        info("checklist.todo 가 없어 기본 준비 항목(D-30 ~ 당일)으로 만듭니다")

    src = outdir / "_checklist.html"
    pdf = outdir / "checklist_A4.pdf"
    for scale in SCALES:
        src.write_text(render(ev, scale), encoding="utf-8")
        html_to_pdf(src, pdf)
        pages = page_count(pdf)
        if pages == 1:
            break
    else:
        warn(f"글자를 {scale:.0%} 까지 줄여도 {pages}장이 됩니다. "
             f"할 일을 줄이거나 행사 파일을 둘로 나눠 만드세요")

    if pages > 1:
        note = f" · {pages}장"
    elif scale < 1.0:
        note = f" · 한 장에 맞추려고 글자를 {scale:.0%} 로 줄였습니다"
    else:
        note = ""
    ok(f"체크리스트 {pdf.name}  (A4{note})")
    # 원본 HTML 은 남겨 둡니다 — 브라우저로 열어 바로 고쳐 인쇄할 수 있습니다
    src.replace(outdir / "checklist.html")
    ok("checklist.html  (브라우저로 열어 수정·인쇄 가능)")


def main() -> None:
    ap = argparse.ArgumentParser(description="준비 체크리스트 생성")
    ap.add_argument("--event", required=True)
    ap.add_argument("--out", default="out/checklist")
    a = ap.parse_args()
    ev = load_event(a.event)
    info(f"행사: {ev.get('title')}")
    build(ev, Path(a.out))
    print(f"\n완료 → {Path(a.out).resolve()}")


if __name__ == "__main__":
    main()
