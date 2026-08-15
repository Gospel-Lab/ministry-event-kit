#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
현수막 만들기 — ministry-event-kit

  python3 scripts/make_banner.py --event examples/event.yml --out out/banner

크기·마감 여백·색·배치는 event.yml 에서 읽고, 없으면 안전한 기본값을 씁니다.
색은 이 파일에 적지 않습니다. 전부 theme.py 에서 옵니다.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import theme  # noqa: E402
from kit import (TEMPLATES, esc, fill, html_to_pdf, info, load_event, ok,  # noqa: E402
                 pdf_to_cmyk_image, warn)

FONT = "Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif"

# 마감 방식별로 글자가 침범하면 안 되는 여백 (mm)
FINISH_MARGIN = {
    "봉미싱":   (150, 80),
    "막대가공": (120, 80),
    "족자":     (80, 80),
    "금속링":   (50, 50),
    "고무":     (50, 50),
    "사방미싱": (30, 30),
    "없음":     (60, 60),
}

LAYOUTS = {
    "center": "가운데 정렬 — 무대 뒤 배경막처럼 정면에서 보는 자리",
    "left":   "왼쪽 정렬 — 옆으로 길고 한쪽에 여백이 필요한 자리",
    "split":  "좌우 나눔 — 왼쪽 제목 · 오른쪽 날짜/장소",
}
MOTIFS = {
    "circuit": "회로 무늬 (기본)",
    "grid":    "격자만",
    "dots":    "점무늬",
    "plain":   "무늬 없음",
}


def circuit(side: str) -> str:
    """회로 장식. 왼쪽 정렬·좌우 나눔에서는 글자와 겹치므로 오른쪽만 그립니다."""
    left = """      <path d="M0 16 H40 L50 11 H86"/>
      <path d="M0 72 H34 L44 78 H80"/>
      <path d="M0 45 H16 L22 38 H30"/>
"""
    right = """      <path d="M400 16 H360 L350 11 H314"/>
      <path d="M400 72 H366 L356 78 H320"/>
      <path d="M400 45 H384 L378 38 H370"/>
"""
    left_d = """      <rect x="86"    y="9.2"  width="3.6" height="3.6" rx=".6"/>
      <rect x="80"    y="76.2" width="3.6" height="3.6" rx=".6"/>
      <rect x="30"    y="36.2" width="3.6" height="3.6" rx=".6"/>
"""
    right_d = """      <rect x="310.4" y="9.2"  width="3.6" height="3.6" rx=".6"/>
      <rect x="316.4" y="76.2" width="3.6" height="3.6" rx=".6"/>
      <rect x="366.4" y="36.2" width="3.6" height="3.6" rx=".6"/>
"""
    paths = (left + right) if side == "both" else right
    dots = (left_d + right_d) if side == "both" else right_d
    return (f'  <g transform="scale({{{{ART_SX}}}}, {{{{ART_SY}}}})">\n'
            f'    <g stroke="{{{{GLOW_LINE}}}}" stroke-width=".3" fill="none" '
            f'opacity=".55" stroke-linecap="square">\n{paths}    </g>\n'
            f'    <g fill="{{{{ACC1}}}}" opacity=".85">\n{dots}    </g>\n'
            f'  </g>')


def build(ev: dict, outdir: Path) -> None:
    b = ev.get("banner") or {}
    outdir.mkdir(parents=True, exist_ok=True)

    trim_w = float(b.get("width_mm", 4000))
    trim_h = float(b.get("height_mm", 900))
    bleed = float(b.get("bleed_mm", 30))
    finish = str(b.get("finish", "봉미싱"))
    safe_x, safe_y = FINISH_MARGIN.get(finish, FINISH_MARGIN["없음"])
    safe_x = float(b.get("safe_x_mm", safe_x))
    safe_y = float(b.get("safe_y_mm", safe_y))

    tk = theme.resolve(ev, warn=warn)
    bn, acc = tk["banner"], tk["accent"]

    layout = str(b.get("layout", "center")).strip().lower()
    if layout not in LAYOUTS:
        if layout:
            warn(f"'{layout}' 은 없는 배치입니다. 쓸 수 있는 값: "
                 f"{' / '.join(LAYOUTS)} → center 로 진행합니다.")
        layout = "center"
    motif = str(b.get("motif", "circuit")).strip().lower()
    if motif not in MOTIFS:
        if motif:
            warn(f"'{motif}' 은 없는 배경무늬입니다. 쓸 수 있는 값: "
                 f"{' / '.join(MOTIFS)} → circuit 으로 진행합니다.")
        motif = "circuit"

    title = str(ev.get("title") or "행사 이름")
    accent_word = str(b.get("accent_word") or "").strip()
    org = str(ev.get("organizer") or "")
    subtitle = str(b.get("subtitle") or "").strip()
    # 날짜·장소를 넣을지. 넣지 않으면 다음 해에도 그대로 쓸 수 있는 상설 현수막이 됩니다.
    show_meta = b.get("show_dates", True)
    dates = str(ev.get("dates") or "").strip()
    place = str(ev.get("place") or "").strip()
    meta = " · ".join(x for x in [dates, place] if x) if show_meta else ""

    # 좌우 나눔은 오른쪽에 넣을 날짜/장소가 있어야 성립합니다
    if layout == "split" and not meta:
        info("오른쪽에 넣을 날짜·장소가 없어 배치를 left 로 바꿉니다")
        layout = "left"

    # 강조 단어가 실제로 눈에 띄는지 미리 봅니다.
    # 강조색이 바탕과 같은 색 계열이거나 제목처럼 밝은 무채색이면 글자가 묻힙니다.
    if accent_word:
        ah, asat, al = theme.hex2hsl(acc["acc"][1])
        bh, bsat, _ = theme.hex2hsl(bn["bg"][3])
        gap = abs((ah - bh + 180) % 360 - 180)
        if al > 0.70 and asat < 0.22:
            warn(f"강조색이 밝은 무채색이라 '{accent_word}' 가 제목과 거의 같아 보입니다. "
                 f"강조 단어를 빼거나 accent 를 gold·copper 처럼 진한 색으로 바꿔 보세요.")
        elif gap < 30 and asat > 0.15 and bsat > 0.15:
            warn(f"강조색이 바탕색과 같은 색 계열({gap:.0f}° 차이)이라 "
                 f"'{accent_word}' 가 눈에 띄지 않습니다. accent 를 바꾸거나 palette 를 바꿔 보세요.")

    # 강조 단어는 제목 끝부분에서 잘라 색을 달리 줍니다
    if accent_word and title.endswith(accent_word):
        head, tail = title[: -len(accent_word)], accent_word
    else:
        head, tail = title, ""

    full_w, full_h = trim_w + bleed * 2, trim_h + bleed * 2
    cx = full_w / 2

    # ── 글자 크기: 안전영역 안에서 최대한 크게 ──
    usable_w = trim_w - safe_x * 2
    right_col = usable_w * 0.26 if layout == "split" else 0.0
    avail_w = usable_w - (right_col + usable_w * 0.04 if layout == "split" else 0.0)
    # 한글 1글자 ≈ 1em, 영문/숫자 ≈ 0.6em 로 어림하고 자간(-5%)을 반영
    em = sum(0.62 if ch.isascii() else 1.0 for ch in title) - len(title) * 0.05
    em = max(em, 1)
    t_size = round(min(avail_w / em, (trim_h - safe_y * 2) * 0.72), 1)
    glyph_h = t_size * 0.72

    org_size = round(min(t_size * 0.30, (trim_h - safe_y * 2) * 0.16), 1)
    sub_size = round(org_size * 0.85, 1)
    meta_size = round(sub_size * 0.92, 1)

    # ── 세로 배치 ──
    # 줄마다 차지하는 높이를 먼저 더하고, 그 덩어리를 재단면 한가운데에 놓습니다.
    # 그런 다음 아래쪽이 안전영역을 넘으면 통째로 위로 올립니다.
    in_block = meta and layout != "split"      # 좌우 나눔이면 날짜는 오른쪽 칸으로 빠집니다
    adv_sub = sub_size * 1.5 if subtitle else 0
    adv_meta = sub_size * 1.5 if in_block else 0
    block_h = org_size + t_size * 0.95 + adv_sub + adv_meta

    cy = bleed + trim_h / 2
    top = cy - block_h / 2
    org_baseline = top + org_size * 0.78
    t_base = org_baseline + t_size * 0.90
    sub_baseline = t_base + adv_sub
    meta_baseline = (sub_baseline if subtitle else t_base) + sub_size * 1.5

    last = meta_baseline if in_block else (sub_baseline if subtitle else t_base)
    overflow = (last + sub_size * 0.3) - (bleed + trim_h - safe_y)
    if overflow > 0:                      # 아래로 넘치면 덩어리 전체를 위로 당깁니다
        org_baseline -= overflow
        t_base -= overflow
        sub_baseline -= overflow
        meta_baseline -= overflow

    org_baseline = round(org_baseline, 1)
    t_base = round(t_base, 1)
    sub_baseline = round(sub_baseline, 1)
    meta_baseline = round(meta_baseline, 1)

    # ── 가로 배치 ──
    left_edge = bleed + safe_x
    right_edge = bleed + trim_w - safe_x
    if layout == "center":
        anchor, ax = "middle", round(cx, 1)
        tx = round(cx - t_size * 0.02, 1)
        halo_cx = round(cx, 1)
    else:
        anchor = "start"
        ax = round(left_edge + t_size * 0.20, 1)   # 세로 막대 자리를 비워 둡니다
        tx = ax
        halo_cx = round(left_edge + avail_w * 0.34, 1)

    # ── 문구 만들기 ──
    parts: list[str] = []

    if layout == "center":
        org_half = (len(org) * org_size * 0.55) / 2
        parts.append(f"""  <g font-family="{FONT}" font-weight="700">
    <line x1="{round(cx - org_half - org_size * 2.4, 1)}" y1="{round(org_baseline - org_size * 0.3, 1)}" x2="{round(cx - org_half - org_size * 0.9, 1)}" y2="{round(org_baseline - org_size * 0.3, 1)}"
          stroke="{acc['acc'][1]}" stroke-width="{round(org_size * 0.03, 2)}" opacity=".8"/>
    <line x1="{round(cx + org_half + org_size * 0.9, 1)}" y1="{round(org_baseline - org_size * 0.3, 1)}" x2="{round(cx + org_half + org_size * 2.4, 1)}" y2="{round(org_baseline - org_size * 0.3, 1)}"
          stroke="{acc['acc'][1]}" stroke-width="{round(org_size * 0.03, 2)}" opacity=".8"/>
    <text x="{round(cx, 1)}" y="{org_baseline}" font-size="{org_size}" letter-spacing="{round(org_size * 0.14, 1)}"
          fill="{acc['acc'][0]}" text-anchor="middle">{esc(org)}</text>
  </g>""")
    else:
        # 왼쪽 정렬·좌우 나눔은 글자 왼쪽에 강조색 세로 막대를 세웁니다
        bar_top = round(org_baseline - org_size * 0.85, 1)
        bar_bot = round((sub_baseline if subtitle else t_base) + sub_size * 0.2, 1)
        parts.append(f"""  <g font-family="{FONT}" font-weight="700">
    <rect x="{round(left_edge, 1)}" y="{bar_top}" width="{round(t_size * 0.045, 1)}" height="{round(bar_bot - bar_top, 1)}"
          rx="{round(t_size * 0.022, 1)}" fill="{acc['acc'][1]}" opacity=".9"/>
    <text x="{ax}" y="{org_baseline}" font-size="{org_size}" letter-spacing="{round(org_size * 0.14, 1)}"
          fill="{acc['acc'][0]}" text-anchor="start">{esc(org)}</text>
  </g>""")

    parts.append(f"""  <g font-family="{FONT}"
     font-weight="900" font-size="{t_size}" letter-spacing="{round(-t_size * 0.05, 1)}" text-anchor="{anchor}">
    <text x="{tx}" y="{round(t_base + t_size * 0.052, 1)}" fill="{bn['shadow'][0]}">{esc(title)}</text>
    <text x="{tx}" y="{round(t_base + t_size * 0.026, 1)}" fill="{bn['shadow'][1]}">{esc(title)}</text>
    <text x="{tx}" y="{t_base}" fill="url(#silver)"
          stroke="{bn['shadow'][1]}" stroke-width="{round(t_size * 0.013, 2)}" paint-order="stroke fill"
      >{esc(head)}<tspan fill="url(#accent)">{esc(tail)}</tspan></text>
  </g>""")

    if subtitle:
        parts.append(f'  <text x="{ax if layout != "center" else round(cx, 1)}" y="{sub_baseline}" '
                     f'font-family="Pretendard, sans-serif" font-weight="500" '
                     f'font-size="{sub_size}" letter-spacing="{round(sub_size * 0.05, 1)}" '
                     f'fill="{bn["sub"]}" text-anchor="{anchor}">{esc(subtitle)}</text>')

    if meta and layout != "split":
        parts.append(f'  <text x="{ax if layout != "center" else round(cx, 1)}" y="{meta_baseline}" '
                     f'font-family="Pretendard, sans-serif" font-weight="600" '
                     f'font-size="{meta_size}" letter-spacing="{round(sub_size * 0.04, 1)}" '
                     f'fill="{acc["acc"][1]}" text-anchor="{anchor}">{esc(meta)}</text>')
    elif layout == "split":
        # 오른쪽 칸: 세로 구분선 + 날짜·장소를 오른쪽 끝에 맞춰 쌓습니다
        rule_x = round(right_edge - right_col - usable_w * 0.02, 1)
        r_top = round(t_base - t_size * 0.80, 1)
        r_bot = round(t_base + t_size * 0.10, 1)
        r_mid = (r_top + r_bot) / 2
        lines = [x for x in (dates, place) if x]
        gap = meta_size * 1.6
        first = r_mid - gap * (len(lines) - 1) / 2 + meta_size * 0.34
        rows = "".join(
            f'\n    <text x="{round(right_edge, 1)}" y="{round(first + i * gap, 1)}" '
            f'font-size="{meta_size}" letter-spacing="{round(meta_size * 0.03, 1)}" '
            f'font-weight="{700 if i == 0 else 500}" '
            f'fill="{acc["acc"][1] if i == 0 else bn["sub"]}" text-anchor="end">{esc(t)}</text>'
            for i, t in enumerate(lines))
        parts.append(f'  <g font-family="Pretendard, sans-serif">'
                     f'\n    <line x1="{rule_x}" y1="{r_top}" x2="{rule_x}" y2="{r_bot}" '
                     f'stroke="{acc["acc"][1]}" stroke-width="{round(t_size * 0.012, 2)}" opacity=".5"/>'
                     f'{rows}\n  </g>')

    # ── 배경 무늬 ──
    if motif == "circuit":
        grid_layer = ('<rect x="0" y="0" width="{{FULL_W}}" height="{{FULL_H}}" '
                      'fill="url(#grid)" mask="url(#gridMask)"/>')
        if layout == "split":
            # 좌우 나눔은 오른쪽 끝까지 날짜 칸이 차지하므로 회로가 글자와 겹칩니다
            info("좌우 나눔 배치에서는 회로 무늬가 날짜와 겹쳐 격자만 남깁니다")
            motif_svg = ""
        else:
            motif_svg = circuit("both" if layout == "center" else "right")
    elif motif == "grid":
        grid_layer = ('<rect x="0" y="0" width="{{FULL_W}}" height="{{FULL_H}}" '
                      'fill="url(#grid)" mask="url(#gridMask)"/>')
        motif_svg = ""
    elif motif == "dots":
        grid_layer = ('<rect x="0" y="0" width="{{FULL_W}}" height="{{FULL_H}}" '
                      'fill="url(#dots)" mask="url(#gridMask)"/>')
        motif_svg = ""
    else:
        grid_layer, motif_svg = "", ""

    grid_mm = round(trim_h / 9, 1)
    v = {
        "TRIM_W": trim_w, "TRIM_H": trim_h, "FULL_W": full_w, "FULL_H": full_h,
        "BLEED": bleed, "SAFE_X": safe_x, "SAFE_Y": safe_y,
        "LAYOUT": layout, "MOTIF_NAME": motif,
        "BG1": bn["bg"][0], "BG2": bn["bg"][1], "BG3": bn["bg"][2], "BG4": bn["bg"][3],
        "GLOW": bn["glow"], "GLOW_LINE": acc["acc"][1], "HALO": bn["halo"],
        "ACC1": acc["acc"][0], "ACC2": acc["acc"][1], "ACC3": acc["acc"][2],
        "HI1": bn["hi"][0], "HI2": bn["hi"][1], "HI3": bn["hi"][2], "HI4": bn["hi"][3],
        "GRIDC": bn["grid"], "GRID": grid_mm, "GRIDW": round(trim_h / 225, 2),
        "DOT_C": round(grid_mm / 2, 1), "DOT_R": round(trim_h / 320, 2),
        "ART_SX": round(full_w / 400, 4), "ART_SY": round(full_h / 90, 4),
        "HALO_CX": halo_cx, "HALO_CY": round(t_base - t_size * 0.35, 1),
        "HALO_RX": round(trim_w * 0.25, 1), "HALO_RY": round(trim_h * 0.32, 1),
        "T_TOP": round(t_base - t_size * 0.78, 1), "T_BOT": round(t_base + t_size * 0.05, 1),
        "GRID_LAYER": grid_layer, "MOTIF": motif_svg, "CONTENT": "\n".join(parts),
    }
    tpl = (TEMPLATES / "banner.svg.tpl").read_text(encoding="utf-8")
    svg = fill(fill(tpl, v), v)          # 무늬 안에 남은 {{FULL_W}} 등을 한 번 더 채웁니다
    svg_path = outdir / "banner.svg"
    svg_path.write_text(svg, encoding="utf-8")
    ok(f"SVG 마스터  {svg_path.name}  ({tk['palette_label']} · {tk['accent_label']} · {layout})")

    wrap = outdir / "_print.html"
    wrap.write_text(
        f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>@page{{size:{trim_w}mm {trim_h}mm;margin:0}}"
        f"html,body{{margin:0;padding:0}}"
        f"img{{display:block;width:{trim_w}mm;height:{trim_h}mm}}</style></head>"
        f"<body><img src='banner.svg'></body></html>", encoding="utf-8")

    pdf = html_to_pdf(wrap, outdir / "banner_print.pdf")
    ok(f"인쇄용 PDF  {pdf.name}  ({trim_w:.0f} × {trim_h:.0f} mm · 도련 없음)")

    # 도련 포함본 — 인쇄소가 재단 여백이 있는 파일을 요구할 때 씁니다
    svg_bleed = svg.replace(
        f'width="{trim_w}mm" height="{trim_h}mm"',
        f'width="{full_w}mm" height="{full_h}mm"').replace(
        f'viewBox="{bleed} {bleed} {trim_w} {trim_h}"',
        f'viewBox="0 0 {full_w} {full_h}"')
    (outdir / "banner_bleed.svg").write_text(svg_bleed, encoding="utf-8")
    wrap_b = outdir / "_print_bleed.html"
    wrap_b.write_text(
        f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<style>@page{{size:{full_w}mm {full_h}mm;margin:0}}"
        f"html,body{{margin:0;padding:0}}"
        f"img{{display:block;width:{full_w}mm;height:{full_h}mm}}</style></head>"
        f"<body><img src='banner_bleed.svg'></body></html>", encoding="utf-8")
    pdf_b = html_to_pdf(wrap_b, outdir / "banner_print_bleed.pdf")
    ok(f"도련 포함본 {pdf_b.name}  ({full_w:.0f} × {full_h:.0f} mm)")
    wrap_b.unlink(missing_ok=True)

    # 큰 현수막은 픽셀 수가 폭발합니다. 5m×2.5m를 150dpi로 만들면 4억 3천만 픽셀이라
    # 변환이 몇 분씩 걸리거나 메모리가 터집니다. 멀리서 보는 인쇄물이라 dpi를 낮춰도
    # 육안 차이가 없으므로, 1억 2천만 픽셀을 넘지 않도록 자동으로 낮춥니다.
    MAX_PX = 120_000_000
    dpi = 150
    px = (trim_w / 25.4 * dpi) * (trim_h / 25.4 * dpi)
    if px > MAX_PX:
        dpi = max(72, int(dpi * (MAX_PX / px) ** 0.5))
        info(f"크기가 커서 해상도를 {dpi}dpi 로 낮춥니다 "
             f"(멀리서 보는 인쇄물이라 육안 차이는 없습니다)")
    jpg_name = f"banner_CMYK_{dpi}dpi.jpg"
    jpg = pdf_to_cmyk_image(pdf, outdir / jpg_name, dpi=dpi)
    if jpg:
        mb = jpg.stat().st_size / 1048576
        ok(f"CMYK 이미지 {jpg.name}  ({mb:.1f} MB, {dpi}dpi)")
    else:
        jpg_name = "(고스트스크립트가 없어 만들지 못했습니다)"
    wrap.unlink(missing_ok=True)

    (outdir / "발주안내.txt").write_text(
        f"""현수막 발주 안내 — {title}

완성 규격 : {trim_w:.0f} × {trim_h:.0f} mm

파일 두 가지 — 주문처가 요구하는 쪽을 고르세요
  banner_print.pdf        {trim_w:.0f} × {trim_h:.0f} mm  도련 없음
                          → "주문 상품과 동일한 실제 사이즈"를 요구하는 온라인 주문처
  banner_print_bleed.pdf  {full_w:.0f} × {full_h:.0f} mm  도련 사방 {bleed:.0f}mm 포함
                          → 재단 여백이 있는 파일을 요구하는 인쇄소
  {jpg_name}  {trim_w:.0f} × {trim_h:.0f} mm  CMYK 이미지 (도련 없음)
마감 방식 : {finish}
문구 여백 : 좌우 {safe_x:.0f}mm · 상하 {safe_y:.0f}mm 안쪽
색상      : CMYK / 해상도 {dpi}dpi · {tk['palette_label']} 바탕에 {tk['accent_label']} 강조
배치      : {layout} ({LAYOUTS[layout]})
타이틀 글자 높이 : 약 {glyph_h:.0f} mm  → 약 {glyph_h/30:.0f} m 거리에서 읽힘

인쇄소에 전달할 말
  "{trim_w/10:.0f}cm × {trim_h/10:.0f}cm 현수막입니다. 실측 100%, CMYK,
   글자와 그라데이션은 모두 래스터라이즈되어 있습니다.
   배경이 어두우니 차광(블랙아웃) 원단으로 부탁드립니다."
""", encoding="utf-8")
    ok("발주안내.txt")


def main() -> None:
    ap = argparse.ArgumentParser(description="현수막 생성")
    ap.add_argument("--event", required=True, help="event.yml 경로")
    ap.add_argument("--out", default="out/banner", help="결과 폴더")
    a = ap.parse_args()
    ev = load_event(a.event)
    info(f"행사: {ev.get('title')}")
    build(ev, Path(a.out))
    print(f"\n완료 → {Path(a.out).resolve()}")


if __name__ == "__main__":
    main()
