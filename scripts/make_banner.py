#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
현수막 만들기 — ministry-event-kit

  python3 scripts/make_banner.py --event examples/event.yml --out out/banner

크기·마감 여백·색은 event.yml 에서 읽고, 없으면 안전한 기본값을 씁니다.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit import (TEMPLATES, esc, fill, html_to_pdf, info, load_event, ok,  # noqa: E402
                 pdf_to_cmyk_image)

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

PALETTES = {
    # 이름: (배경4, 발광, 강조3, 후광, 격자색, 그림자2)
    "plum": (["#0d0513", "#25092f", "#3b0d52", "#4f126b"], "#8f2ac4",
             ["#f9efd8", "#e2cb98", "#b8955b"], "#c78ae8", "#d8c9ec",
             ["#341a58", "#13081f"]),
    "navy": (["#050a16", "#0b1730", "#12244d", "#183165"], "#2a5bd7",
             ["#f7ecd2", "#e0c894", "#b8955b"], "#7ba3e8", "#c9d6ee",
             ["#12203f", "#070d1c"]),
    "forest": (["#04120c", "#082018", "#0d3226", "#114434"], "#1d8a63",
               ["#f4ecd2", "#dfc994", "#b3935c"], "#6fd4a8", "#c6e2d5",
               ["#0d2b20", "#05140e"]),
    "wine": (["#140409", "#2a0714", "#420c20", "#59102c"], "#b02a55",
             ["#f9e8d2", "#e3c396", "#bb9159"], "#e8829f", "#eccdd6",
             ["#3a0f1e", "#180510"]),
}


def build(ev: dict, outdir: Path) -> None:
    b = ev.get("banner") or {}
    brand = ev.get("brand") or {}
    outdir.mkdir(parents=True, exist_ok=True)

    trim_w = float(b.get("width_mm", 4000))
    trim_h = float(b.get("height_mm", 900))
    bleed = float(b.get("bleed_mm", 30))
    finish = str(b.get("finish", "봉미싱"))
    safe_x, safe_y = FINISH_MARGIN.get(finish, FINISH_MARGIN["없음"])
    safe_x = float(b.get("safe_x_mm", safe_x))
    safe_y = float(b.get("safe_y_mm", safe_y))

    pal_name = str(brand.get("palette", "plum"))
    pal = PALETTES.get(pal_name, PALETTES["plum"])
    bg, glow, acc, halo, gridc, shadow = pal

    title = str(ev.get("title") or "행사 이름")
    accent_word = str(b.get("accent_word") or "").strip()
    org = str(ev.get("organizer") or "")
    subtitle = str(b.get("subtitle") or "").strip()
    # 날짜·장소를 넣을지. 넣지 않으면 다음 해에도 그대로 쓸 수 있는 상설 현수막이 됩니다.
    show_meta = b.get("show_dates", True)
    meta = " · ".join(x for x in [str(ev.get("dates") or "").strip(),
                                  str(ev.get("place") or "").strip()] if x) if show_meta else ""

    # 강조 단어는 제목 끝부분에서 잘라 색을 달리 줍니다
    if accent_word and title.endswith(accent_word):
        head, tail = title[: -len(accent_word)], accent_word
    else:
        head, tail = title, ""

    full_w, full_h = trim_w + bleed * 2, trim_h + bleed * 2
    cx = full_w / 2

    # ── 글자 크기: 안전영역 안에서 최대한 크게 ──
    usable_w = trim_w - safe_x * 2
    # 한글 1글자 ≈ 1em, 영문/숫자 ≈ 0.6em 로 어림하고 자간(-5%)을 반영
    em = sum(0.62 if ch.isascii() else 1.0 for ch in title) - len(title) * 0.05
    em = max(em, 1)
    t_size = min(usable_w / em, (trim_h - safe_y * 2) * 0.72)
    t_size = round(t_size, 1)
    glyph_h = t_size * 0.72

    org_size = round(min(t_size * 0.30, (trim_h - safe_y * 2) * 0.16), 1)
    sub_size = round(org_size * 0.85, 1)

    # ── 세로 배치 ──
    # 줄마다 차지하는 높이를 먼저 더하고, 그 덩어리를 재단면 한가운데에 놓습니다.
    # 그런 다음 아래쪽이 안전영역을 넘으면 통째로 위로 올립니다.
    adv_org = org_size * 1.0
    adv_title = t_size * 0.95
    adv_sub = sub_size * 1.5 if subtitle else 0
    adv_meta = sub_size * 1.5 if meta else 0
    block_h = adv_org + adv_title + adv_sub + adv_meta

    cy = bleed + trim_h / 2
    top = cy - block_h / 2
    org_baseline = top + org_size * 0.78
    t_base = org_baseline + t_size * 0.90
    sub_baseline = t_base + (sub_size * 1.5 if subtitle else 0)
    meta_baseline = (sub_baseline if subtitle else t_base) + sub_size * 1.5

    last_baseline = meta_baseline if meta else (sub_baseline if subtitle else t_base)
    bottom_limit = bleed + trim_h - safe_y
    overflow = (last_baseline + sub_size * 0.3) - bottom_limit
    if overflow > 0:                      # 아래로 넘치면 덩어리 전체를 위로 당깁니다
        org_baseline -= overflow
        t_base -= overflow
        sub_baseline -= overflow
        meta_baseline -= overflow

    org_baseline = round(org_baseline, 1)
    t_base = round(t_base, 1)
    sub_baseline = round(sub_baseline, 1)
    meta_baseline = round(meta_baseline, 1)

    org_half = (len(org) * org_size * 0.55) / 2
    v = {
        "TRIM_W": trim_w, "TRIM_H": trim_h, "FULL_W": full_w, "FULL_H": full_h,
        "BLEED": bleed, "SAFE_X": safe_x, "SAFE_Y": safe_y, "CX": round(cx, 1),
        "BG1": bg[0], "BG2": bg[1], "BG3": bg[2], "BG4": bg[3], "GLOW": glow,
        "ACC1": acc[0], "ACC2": acc[1], "ACC3": acc[2], "HALO": halo,
        "GRIDC": gridc, "GRID": round(trim_h / 9, 1), "GRIDW": round(trim_h / 225, 2),
        "SHADOW1": shadow[0], "SHADOW2": shadow[1],
        "ART_SX": round(full_w / 400, 4), "ART_SY": round(full_h / 90, 4),
        "HALO_CY": round(t_base - t_size * 0.35, 1),
        "HALO_RX": round(trim_w * 0.25, 1), "HALO_RY": round(trim_h * 0.32, 1),
        "ORG": esc(org), "ORG_SIZE": org_size, "ORG_Y": org_baseline,
        "ORG_LS": round(org_size * 0.14, 1), "ORG_LW": round(org_size * 0.03, 2),
        "ORG_LY": round(org_baseline - org_size * 0.3, 1),
        "ORG_L1": round(cx - org_half - org_size * 2.4, 1),
        "ORG_L2": round(cx - org_half - org_size * 0.9, 1),
        "ORG_R1": round(cx + org_half + org_size * 0.9, 1),
        "ORG_R2": round(cx + org_half + org_size * 2.4, 1),
        "T_SIZE": t_size, "T_LS": round(-t_size * 0.05, 1),
        "TX": round(cx - t_size * 0.02, 1),
        "T_Y1": t_base, "T_Y2": round(t_base + t_size * 0.026, 1),
        "T_Y3": round(t_base + t_size * 0.052, 1),
        "T_STROKE": round(t_size * 0.013, 2),
        "T_TOP": round(t_base - t_size * 0.78, 1), "T_BOT": round(t_base + t_size * 0.05, 1),
        "TITLE_PLAIN": esc(title), "TITLE_HEAD": esc(head), "TITLE_ACCENT": esc(tail),
        "SUBTITLE_BLOCK": "", "META_BLOCK": "",
    }
    if subtitle:
        v["SUBTITLE_BLOCK"] = (
            f'<text x="{round(cx,1)}" y="{sub_baseline}" '
            f'font-family="Pretendard, sans-serif" font-weight="500" '
            f'font-size="{sub_size}" letter-spacing="{round(sub_size*0.05,1)}" '
            f'fill="#c6b6dc" text-anchor="middle">{esc(subtitle)}</text>')
    if meta:
        my = meta_baseline
        v["META_BLOCK"] = (
            f'<text x="{round(cx,1)}" y="{my}" '
            f'font-family="Pretendard, sans-serif" font-weight="600" '
            f'font-size="{round(sub_size*0.92,1)}" letter-spacing="{round(sub_size*0.04,1)}" '
            f'fill="{acc[1]}" text-anchor="middle">{esc(meta)}</text>')

    svg = fill((TEMPLATES / "banner.svg.tpl").read_text(encoding="utf-8"), v)
    svg_path = outdir / "banner.svg"
    svg_path.write_text(svg, encoding="utf-8")
    ok(f"SVG 마스터  {svg_path.name}")

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
    jpg = pdf_to_cmyk_image(pdf, outdir / f"banner_CMYK_{dpi}dpi.jpg", dpi=dpi)
    if jpg:
        mb = jpg.stat().st_size / 1048576
        ok(f"CMYK 이미지 {jpg.name}  ({mb:.1f} MB, {dpi}dpi)")
    wrap.unlink(missing_ok=True)

    (outdir / "발주안내.txt").write_text(
        f"""현수막 발주 안내 — {title}

완성 규격 : {trim_w:.0f} × {trim_h:.0f} mm

파일 두 가지 — 주문처가 요구하는 쪽을 고르세요
  banner_print.pdf        {trim_w:.0f} × {trim_h:.0f} mm  도련 없음
                          → "주문 상품과 동일한 실제 사이즈"를 요구하는 온라인 주문처
  banner_print_bleed.pdf  {full_w:.0f} × {full_h:.0f} mm  도련 사방 {bleed:.0f}mm 포함
                          → 재단 여백이 있는 파일을 요구하는 인쇄소
  banner_CMYK_150dpi.jpg  {trim_w:.0f} × {trim_h:.0f} mm  CMYK 이미지 (도련 없음)
마감 방식 : {finish}
문구 여백 : 좌우 {safe_x:.0f}mm · 상하 {safe_y:.0f}mm 안쪽
색상      : CMYK / 해상도 {dpi}dpi
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
