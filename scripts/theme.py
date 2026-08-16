#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
색을 결정하는 곳 — ministry-event-kit

현수막·명찰·랜딩페이지의 모든 색이 여기서 나옵니다.
다른 파일에는 색을 직접 적지 않습니다. 그래야 색을 바꿨을 때 셋이 따로 놀지 않습니다.

event.yml 에서 읽는 것 — 세 가지 방법 중 하나를 쓰면 됩니다.

  brand:
    palette: navy            ① 준비된 색 묶음 (plum / navy / forest / wine / slate / clay)

  brand:
    palette: navy
    accent: silver           ② 강조색만 따로 (gold / silver / white / copper / 직접 #hex)

  brand:
    colors:
      base:   "#0a2f3a"      ③ 아무 색이나 직접. 나머지 수십 가지 색은 이 두 개에서 계산합니다.
      accent: "#e0b96a"

①은 지금까지와 똑같이 나옵니다. ②③은 새로 생긴 길입니다.
"""
from __future__ import annotations

import colorsys
import re

# ─────────────────────────────────────────────────────────────
# 색 계산 도구
# ─────────────────────────────────────────────────────────────


def hex2hsl(h: str) -> tuple[float, float, float]:
    raw = h.strip()
    h = raw.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        raise ValueError(f"색 표기가 잘못됐습니다: {raw!r}")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    return hh * 360, ss, ll


def hsl(h: float, s: float, l: float) -> str:
    """색상각·채도·밝기로 #rrggbb 를 만듭니다. 범위를 벗어난 값은 잘라냅니다."""
    h = h % 360
    s = min(max(s, 0.0), 1.0)
    l = min(max(l, 0.0), 1.0)
    r, g, b = colorsys.hls_to_rgb(h / 360, l, s)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def rgb_of(hexcode: str) -> str:
    """rgba() 안에 넣을 '123,79,192' 형태."""
    c = hexcode.lstrip("#")
    if len(c) == 3:
        c = "".join(x * 2 for x in c)
    return ",".join(str(int(c[i:i + 2], 16)) for i in (0, 2, 4))


# ─────────────────────────────────────────────────────────────
# ① 준비된 색 묶음 — 값을 그대로 적어 둡니다
#    (계산으로 만들지 않는 이유: 지금까지 만든 인쇄물과 한 픽셀도 달라지면 안 됩니다)
# ─────────────────────────────────────────────────────────────

PRESETS: dict[str, dict] = {
    "plum": {
        "label": "보라",
        "base": "#4f126b",
        "banner": dict(
            bg=["#0d0513", "#25092f", "#3b0d52", "#4f126b"], glow="#8f2ac4",
            halo="#c78ae8", grid="#d8c9ec", shadow=["#341a58", "#13081f"],
            hi=["#ffffff", "#f2effa", "#d0c9e8", "#b3a2cc"], sub="#c6b6dc",
            acc=["#f9efd8", "#e2cb98", "#b8955b"]),
        "badge": dict(
            deep="#5f34a6", mid="#8a52d2", light="#bb8cec", ink="#2e1348",
            ink2="#6b5b8a", ink3="#8d7fae", card="#f3ecfc", card2="#fbf8fe",
            card3="#faf7fe", rule="#ece3f7", cut="#c9b8e4", body="#33174f",
            role="#7b4fc0", role_deep="#6533b0", role_mid="#8f5fd0",
            tint="123,79,192", chip_on="#2c1342", band="#a97ce0"),
        "landing": dict(
            ink="#2e1348", deep="#5f34a6", mid="#9c62dd", paper="#f7f3fd",
            ink2="#5b5170", ink3="#8d84a3", rule="#e3dcf0",
            hero_text="#e6ddf7", hero_dim="#d6c9ef"),
    },
    "navy": {
        "label": "남색",
        "base": "#183165",
        "banner": dict(
            bg=["#050a16", "#0b1730", "#12244d", "#183165"], glow="#2a5bd7",
            halo="#7ba3e8", grid="#c9d6ee", shadow=["#12203f", "#070d1c"],
            hi=["#ffffff", "#eef2fa", "#c9d3e8", "#a3aecc"], sub="#b6c4dc",
            acc=["#f7ecd2", "#e0c894", "#b8955b"]),
        "badge": dict(
            deep="#1b3a6b", mid="#2f5fa8", light="#7ba3e8", ink="#0f2440",
            ink2="#4a5d7a", ink3="#7f8da3", card="#e9f0fa", card2="#f6f9fd",
            card3="#f5f8fc", rule="#e0e8f3", cut="#b8c8e0", body="#132b4d",
            role="#2f5fa8", role_deep="#1b3a6b", role_mid="#3f74c4",
            tint="43,79,140", chip_on="#0f2440", band="#7ba3e8"),
        "landing": dict(
            ink="#0d1b33", deep="#1b3a6b", mid="#3f6fb5", paper="#f2f5fa",
            ink2="#42506b", ink3="#7d879c", rule="#dce3ee",
            hero_text="#dde6f5", hero_dim="#c6d3e8"),
    },
    "forest": {
        "label": "녹색",
        "base": "#114434",
        "banner": dict(
            bg=["#04120c", "#082018", "#0d3226", "#114434"], glow="#1d8a63",
            halo="#6fd4a8", grid="#c6e2d5", shadow=["#0d2b20", "#05140e"],
            hi=["#ffffff", "#eef8f3", "#c9e2d8", "#a3c0b4"], sub="#b3d2c4",
            acc=["#f4ecd2", "#dfc994", "#b3935c"]),
        "badge": dict(
            deep="#14513a", mid="#2b8462", light="#6fd4a8", ink="#0d2b20",
            ink2="#456a5c", ink3="#78968a", card="#e7f4ee", card2="#f5fbf8",
            card3="#f4faf7", rule="#dcede5", cut="#aed0c0", body="#12362a",
            role="#2b8462", role_deep="#14513a", role_mid="#37a077",
            tint="30,110,80", chip_on="#0d2b20", band="#6fd4a8"),
        "landing": dict(
            ink="#0d2b20", deep="#14513a", mid="#2b8462", paper="#f1f7f4",
            ink2="#3e5c50", ink3="#7a9188", rule="#d9e8e1",
            hero_text="#dcefe6", hero_dim="#c2ddd2"),
    },
    "wine": {
        "label": "자주",
        "base": "#59102c",
        "banner": dict(
            bg=["#140409", "#2a0714", "#420c20", "#59102c"], glow="#b02a55",
            halo="#e8829f", grid="#eccdd6", shadow=["#3a0f1e", "#180510"],
            hi=["#ffffff", "#faeef2", "#e4c9d3", "#c2a3ae"], sub="#dcb6c4",
            acc=["#f9e8d2", "#e3c396", "#bb9159"]),
        "badge": dict(
            deep="#6b1230", mid="#a83057", light="#e08aa4", ink="#2a0714",
            ink2="#77505f", ink3="#9c7c88", card="#fbeaf0", card2="#fdf6f8",
            card3="#fdf5f7", rule="#f4e0e7", cut="#e0b8c6", body="#3a1020",
            role="#a83057", role_deep="#6b1230", role_mid="#c04a72",
            tint="150,40,75", chip_on="#2a0714", band="#e08aa4"),
        "landing": dict(
            ink="#2a0714", deep="#6b1230", mid="#a83057", paper="#fbf2f5",
            ink2="#6b4b56", ink3="#9c848d", rule="#eedbe2",
            hero_text="#f5dde5", hero_dim="#e8c6d1"),
    },
    # 아래 둘은 계산으로 만듭니다. 준비된 이름을 늘리면서도 표를 손으로 늘리지 않기 위해서입니다.
    "slate": {"label": "청회색", "base": "#2b3a4a", "derive": True},
    "clay":  {"label": "황토",   "base": "#5c3a1e", "derive": True},
}

# ─────────────────────────────────────────────────────────────
# ② 강조색
#    gold 는 색 묶음마다 미세하게 다른 금색을 쓰므로 값을 두지 않고 "그대로" 로 둡니다.
# ─────────────────────────────────────────────────────────────

ACCENTS: dict[str, dict] = {
    "gold":   {"label": "금색", "keep": True},
    "silver": {"label": "은색", "hex": "#c3cbd4"},
    "white":  {"label": "흰색", "hex": "#e8e8ec"},
    "copper": {"label": "구릿빛", "hex": "#c47f4e"},
}


def accent_tokens(acc_hex: str) -> dict:
    """강조색 하나에서 세 가지 산출물이 쓸 색을 모두 만듭니다."""
    h, s, l = hex2hsl(acc_hex)
    return {
        # 현수막 타이틀 강조 글자 (위→아래 그라데이션)
        "acc": [hsl(h + 2, min(s + 0.15, 1), min(l + 0.17, 0.96)),
                hsl(h, s, l),
                hsl(h - 3, max(s - 0.20, 0.10), max(l - 0.20, 0.18))],
        # 명찰 참가자 배지 · 금색 띠
        "chip": [hsl(h + 2, min(s + 0.08, 1), min(l + 0.05, 0.92)), hsl(h, s, l)],
        "bar":  [hsl(h, s, l), hsl(h + 2, min(s + 0.12, 1), min(l + 0.13, 0.94))],
        # 명찰 머리말 글자 (강조색 계열의 밝은 쪽)
        "org": hsl(h, min(s + 0.05, 1), min(l + 0.22, 0.88)),
        # 테두리 선에 쓰는 rgba 앞부분
        "line": rgb_of(hsl(h, max(s - 0.20, 0.08), max(l - 0.20, 0.30))),
    }


def _accent_from_preset(acc3: list[str]) -> dict:
    """색 묶음이 이미 갖고 있는 금색 3단에서 나머지를 만듭니다 (지금까지의 값 유지)."""
    return {
        "acc": list(acc3),
        "chip": ["#ecd69f", "#c9a86a"],
        "bar":  ["#c9a86a", "#eddcb4"],
        "org":  "#f2ddb4",
        "line": "184,149,91",
    }


# ─────────────────────────────────────────────────────────────
# ③ 아무 색에서 전체를 계산하기
# ─────────────────────────────────────────────────────────────

def derive(base_hex: str) -> dict:
    """바탕색 하나로 현수막·명찰·랜딩페이지가 쓸 색을 전부 만듭니다.

    밝기(l)는 어두운 쪽으로 잡습니다. 현수막 배경은 어둡고 글자가 밝다는 전제 위에
    전체 디자인이 서 있기 때문입니다. 밝은 색을 주면 어둡게 낮추고 알려 드립니다.
    """
    h, s, l = hex2hsl(base_hex)
    s = min(max(s, 0.28), 0.82)          # 너무 흐리거나 형광이면 잡아 줍니다
    l = min(max(l, 0.14), 0.30)

    return {
        "banner": dict(
            bg=[hsl(h, s * 0.85, l * 0.20), hsl(h, s * 0.95, l * 0.44),
                hsl(h, s, l * 0.76), hsl(h, s, l)],
            glow=hsl(h, min(s + 0.05, 0.85), 0.46),
            halo=hsl(h, min(s + 0.03, 0.80), 0.73),
            grid=hsl(h, 0.40, 0.86),
            shadow=[hsl(h, s * 0.80, 0.22), hsl(h, s * 0.90, 0.08)],
            hi=["#ffffff", hsl(h, 0.45, 0.96), hsl(h, 0.32, 0.85), hsl(h, 0.24, 0.72)],
            sub=hsl(h, 0.30, 0.79),
        ),
        "badge": dict(
            deep=hsl(h, s * 0.80, 0.29), mid=hsl(h, s * 0.78, 0.42),
            light=hsl(h, s * 0.85, 0.70), ink=hsl(h, s * 0.85, 0.15),
            ink2=hsl(h, 0.20, 0.45), ink3=hsl(h, 0.15, 0.58),
            card=hsl(h, 0.55, 0.95), card2=hsl(h, 0.50, 0.98),
            card3=hsl(h, 0.45, 0.975), rule=hsl(h, 0.35, 0.92),
            cut=hsl(h, 0.30, 0.80), body=hsl(h, s * 0.75, 0.19),
            role=hsl(h, s * 0.72, 0.40), role_deep=hsl(h, s * 0.80, 0.30),
            role_mid=hsl(h, s * 0.72, 0.48),
            tint=rgb_of(hsl(h, s * 0.72, 0.40)), chip_on=hsl(h, s * 0.85, 0.15), band=hsl(h, s * 0.85, 0.70),
        ),
        "landing": dict(
            ink=hsl(h, s * 0.85, 0.15), deep=hsl(h, s * 0.80, 0.29),
            mid=hsl(h, s * 0.75, 0.47), paper=hsl(h, 0.45, 0.97),
            ink2=hsl(h, 0.16, 0.38), ink3=hsl(h, 0.13, 0.58),
            rule=hsl(h, 0.35, 0.90),
            hero_text=hsl(h, 0.45, 0.92), hero_dim=hsl(h, 0.40, 0.86),
        ),
    }


# ─────────────────────────────────────────────────────────────
# 행사 성격 → 디자인
#   근거와 출처는 docs/design-rules.md 에 정리해 두었습니다.
#   여기에는 결과 수치만 둡니다.
# ─────────────────────────────────────────────────────────────

# 대상. type_scale 은 본문 글자 배율입니다.
AUDIENCE = {
    "어린이":   dict(type_scale=1.06, prefer=["wine", "plum"], accent="gold",
                     motif="dots", note="밝은 배경이 필요한 대상입니다"),
    "청소년":   dict(type_scale=1.00, prefer=["plum", "wine"], accent="gold",
                     motif="circuit"),
    "청년":     dict(type_scale=1.00, prefer=["navy", "plum"], accent="gold",
                     motif="circuit", layout="split"),
    "장년":     dict(type_scale=1.08, prefer=["navy", "forest"], accent="gold",
                     motif="grid"),
    # 대비 감도가 40세부터 떨어져 80세에는 최대 83% 낮아집니다.
    # 글자를 키우는 것보다 대비를 높이는 것이 먼저입니다.
    "어르신":   dict(type_scale=1.15, prefer=["navy", "forest"], accent="gold",
                     motif="grid", contrast=True),
    "전교인":   dict(type_scale=1.08, prefer=["plum", "navy"], accent="gold",
                     motif="circuit"),
    "외부초청": dict(type_scale=1.08, prefer=["navy", "slate"], accent="gold",
                     motif="grid", cta=True),
}
AUDIENCE_ALIAS = {"어른": "장년", "성인": "장년", "노인": "어르신", "시니어": "어르신",
                  "유치부": "어린이", "유년부": "어린이", "초등": "어린이",
                  "중고등": "청소년", "학생": "청소년", "새가족": "외부초청",
                  "전교인 대상": "전교인", "온세대": "전교인"}

MOOD = {
    "경건": dict(prefer=["navy", "plum"],   accent="gold",   motif="grid"),
    "활기": dict(prefer=["wine", "plum"],   accent="gold",   motif="circuit"),
    "따뜻": dict(prefer=["clay", "wine"],   accent="gold",   motif="dots"),
    "장중": dict(prefer=["navy", "slate"],  accent="silver", motif="plain"),
}
MOOD_ALIAS = {"차분": "경건", "엄숙": "장중", "신나는": "활기", "밝은": "활기",
              "포근": "따뜻", "정중": "장중"}

FORMALITY = {"격식": 1.10, "보통": 1.00, "편안": 0.94}   # 여백 배율


def brief_of(ev: dict) -> dict:
    """event.yml 의 brief 를 읽어 실제로 쓸 값으로 정리합니다.

    brief 가 없으면 전부 중립값입니다. 즉 지금까지의 결과물이 그대로 나옵니다.
    """
    b = ev.get("brief") or {}
    if not isinstance(b, dict):
        b = {}
    aud = str(b.get("audience") or "").strip()
    aud = AUDIENCE_ALIAS.get(aud, aud)
    mood = str(b.get("mood") or "").strip()
    mood = MOOD_ALIAS.get(mood, mood)
    form = str(b.get("formality") or "보통").strip()

    a = AUDIENCE.get(aud, {})
    m = MOOD.get(mood, {})
    return {
        "audience": aud if aud in AUDIENCE else "",
        "mood": mood if mood in MOOD else "",
        "formality": form if form in FORMALITY else "보통",
        # 글자 배율 — 명찰과 랜딩페이지 본문에 걸립니다
        "type_scale": float(a.get("type_scale", 1.0)),
        "space": FORMALITY.get(form, 1.0),
        "contrast": bool(a.get("contrast")),
        "cta": bool(a.get("cta")),
        # 아무것도 정하지 않았을 때 채울 값
        # 색 묶음은 대상이 먼저입니다 — 가독성이 분위기보다 앞섭니다.
        # 강조색과 무늬는 분위기가 먼저입니다 — 그쪽이 톤을 만듭니다.
        "prefer": a.get("prefer") or m.get("prefer") or [],
        "accent": m.get("accent") or a.get("accent") or "",
        "motif": m.get("motif") or a.get("motif") or "",
        "layout": a.get("layout") or "",
        "note": a.get("note", ""),
    }


# ─────────────────────────────────────────────────────────────
# 바깥에서 부르는 곳
# ─────────────────────────────────────────────────────────────

# CMYK 로 옮길 때 남색으로 빠지는 색상각 (README 의 함정 2번)
RISKY_HUE = (243, 264)


def resolve(ev: dict, warn=None) -> dict:
    """event.yml 의 brand 항목을 읽어 세 산출물이 쓸 색을 한 번에 정합니다.

    반환값: {"banner": {...}, "badge": {...}, "landing": {...},
             "accent_label": "금색", "palette_label": "보라"}
    """
    brand = (ev.get("brand") or {}) if isinstance(ev.get("brand"), dict) else {}
    colors = brand.get("colors") or {}
    if not isinstance(colors, dict):
        colors = {}
    bf = brief_of(ev)

    base_hex = str(colors.get("base") or colors.get("bg") or "").strip()
    # 색 코드가 잘못돼 있으면 멈추지 않고 알려준 뒤 준비된 색으로 갑니다.
    # 여기서 예외를 그대로 두면 오타 한 글자에 파이썬 추적이 뜹니다.
    if base_hex:
        try:
            hex2hsl(base_hex)
        except ValueError as e:
            if warn:
                warn(f"{e} — brand.colors.base 를 무시하고 준비된 색으로 진행합니다. "
                     f"색은 #rrggbb 여섯 자리로 적어 주세요 (예: \"#0a2f3a\")")
            base_hex = ""
    # 직접 정한 값이 항상 이깁니다. brief 는 비어 있는 자리만 채웁니다.
    pal_name = str(brand.get("palette") or "").strip()
    if not pal_name and not base_hex and bf["prefer"]:
        pal_name = bf["prefer"][0]
    pal_name = pal_name or "plum"

    # ── 바탕색 ──
    if base_hex:
        raw_h, raw_s, raw_l = hex2hsl(base_hex)
        tok = derive(base_hex)
        pal_label = "직접 지정"
        if raw_l > 0.34 and warn:
            warn(f"바탕색이 밝아서({raw_l*100:.0f}%) 어둡게 낮췄습니다. "
                 f"현수막은 어두운 바탕에 밝은 글자를 전제로 만들어져 있습니다.")
        if RISKY_HUE[0] <= raw_h <= RISKY_HUE[1] and warn:
            warn(f"이 청보라(색상각 {raw_h:.0f}°)는 인쇄(CMYK)에서 남색으로 빠집니다. "
                 f"화면과 다르게 나와도 괜찮은지 확인하시거나 275~285° 로 옮겨 보세요.")
        default_acc = "#c9a86a"
    else:
        preset = PRESETS.get(pal_name)
        if preset is None:
            if warn:
                warn(f"'{pal_name}' 은 없는 색 이름입니다. "
                     f"쓸 수 있는 이름: {' / '.join(PRESETS)} → plum 으로 진행합니다.")
            pal_name, preset = "plum", PRESETS["plum"]
        pal_label = preset["label"]
        if preset.get("derive"):
            tok = derive(preset["base"])
        else:
            tok = {k: {kk: (list(vv) if isinstance(vv, list) else vv)
                       for kk, vv in preset[k].items()}
                   for k in ("banner", "badge", "landing")}
        # 표에 금색 3단이 적혀 있으면 그대로 쓰고, 계산으로 만든 색 묶음이면 기본 금색을 씁니다
        default_acc = None if "acc" in tok["banner"] else "#c9a86a"

    # ── 강조색 ──
    acc_name = str(brand.get("accent") or colors.get("accent") or "").strip()
    if acc_name.startswith("#"):
        try:
            hex2hsl(acc_name)
        except ValueError as e:
            if warn:
                warn(f"{e} — 강조색을 금색으로 대신합니다.")
            acc_name = ""
    if not acc_name and not base_hex:
        acc_name = bf["accent"]
    if acc_name.startswith("#"):
        acc = accent_tokens(acc_name)
        acc_label = "직접 지정"
    elif acc_name and acc_name.lower() in ACCENTS:
        spec = ACCENTS[acc_name.lower()]
        acc_label = spec["label"]
        if spec.get("keep") and default_acc is None:
            acc = _accent_from_preset(tok["banner"]["acc"])
        else:
            acc = accent_tokens(spec.get("hex") or default_acc or "#c9a86a")
    else:
        if acc_name and warn:
            warn(f"'{acc_name}' 은 없는 강조색입니다. "
                 f"쓸 수 있는 이름: {' / '.join(ACCENTS)} 또는 #rrggbb → 금색으로 진행합니다.")
        acc_label = ACCENTS["gold"]["label"]
        if default_acc is None:
            acc = _accent_from_preset(tok["banner"]["acc"])
        else:
            acc = accent_tokens(default_acc)

    tok["banner"]["acc"] = acc["acc"]
    tok["accent"] = acc
    tok["accent_label"] = acc_label
    tok["palette_label"] = pal_label
    tok["brief"] = bf
    return tok
