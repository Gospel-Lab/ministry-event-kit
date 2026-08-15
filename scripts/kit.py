#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ministry-event-kit 공통 엔진

한 곳에 모아둔 이유: 현수막·명찰·포스터가 전부 같은 경로를 씁니다.
  템플릿(HTML/SVG) → 값 채우기 → 크롬으로 실측 PDF → (선택) CMYK 래스터

표준 라이브러리만으로 동작하고, Pillow가 있으면 CMYK/PNG까지 처리합니다.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"

MM_PER_IN = 25.4


# ────────────────────────────── 크롬 찾기 ──────────────────────────────
CHROME_CANDIDATES = [
    os.environ.get("CHROME_PATH", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/snap/bin/chromium",
]


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if c and Path(c).exists():
            return c
    for name in ("google-chrome", "chromium", "chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    raise SystemExit(
        "크롬을 찾지 못했습니다.\n"
        "  · 맥/윈도우: 구글 크롬을 설치하세요 (https://google.com/chrome)\n"
        "  · 이미 있다면 CHROME_PATH 환경변수로 실행 파일 경로를 알려주세요"
    )


def find_ghostscript() -> str | None:
    for name in ("gs", "gswin64c", "gswin32c"):
        p = shutil.which(name)
        if p:
            return p
    for c in ("/opt/homebrew/bin/gs", "/usr/local/bin/gs"):
        if Path(c).exists():
            return c
    return None


# ────────────────────────────── 템플릿 채우기 ──────────────────────────────
def fill(text: str, values: dict) -> str:
    """{{KEY}} 자리를 값으로 바꿉니다. 없는 키는 빈 문자열로 지웁니다."""
    def sub(m):
        key = m.group(1).strip()
        v = values.get(key, "")
        return "" if v is None else str(v)
    return re.sub(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}", sub, text)


def esc(s) -> str:
    """HTML/SVG 안에 값을 넣을 때 깨지지 않게 합니다."""
    if s is None:
        return ""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def load_event(path: str | Path) -> dict:
    """event.yml 또는 event.json 을 읽습니다.

    PyYAML이 없어도 동작하도록 흔히 쓰는 문법만 지원하는 작은 파서를 씁니다
    (key: value / 2단 들여쓰기 / - 목록 / # 주석).
    """
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        return json.loads(raw)
    try:
        import yaml  # type: ignore
        return yaml.safe_load(raw) or {}
    except ImportError:
        return _mini_yaml(raw)


def _mini_yaml(raw: str) -> dict:
    root: dict = {}
    stack = [(-1, root)]
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        line_s = line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if line_s.startswith("- "):
            item = line_s[2:].strip()
            if not isinstance(parent, list):
                continue
            parent.append(_scalar(item))
            continue
        if ":" not in line_s:
            continue
        key, _, val = line_s.partition(":")
        key, val = key.strip(), val.strip()
        if val == "":
            nxt: dict | list = {}
            parent[key] = nxt
            stack.append((indent, nxt))
            # 다음 줄이 '- '로 시작하면 목록으로 바꿔 담는다
            parent[key] = nxt
        else:
            parent[key] = _scalar(val)
    return _fix_lists(raw, root)


def _scalar(v: str):
    v = v.strip().strip('"').strip("'")
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def _fix_lists(raw: str, tree: dict) -> dict:
    """_mini_yaml 보조 — '키:' 다음 줄이 '- '면 목록으로 만든다."""
    lines = [l for l in raw.splitlines() if l.strip() and not l.lstrip().startswith("#")]
    for i, line in enumerate(lines[:-1]):
        if line.strip().endswith(":"):
            nxt = lines[i + 1]
            if nxt.strip().startswith("- "):
                key = line.strip()[:-1].strip()
                indent = len(nxt) - len(nxt.lstrip())
                items = []
                for l in lines[i + 1:]:
                    ind = len(l) - len(l.lstrip())
                    if not l.strip().startswith("- ") or ind != indent:
                        break
                    items.append(_scalar(l.strip()[2:]))
                _set_deep(tree, key, items)
    return tree


def _set_deep(tree, key, value):
    if key in tree and not isinstance(tree[key], list):
        tree[key] = value
        return True
    for v in tree.values():
        if isinstance(v, dict) and _set_deep(v, key, value):
            return True
    return False


# ────────────────────────────── 렌더링 ──────────────────────────────
def html_to_pdf(html_path: Path, pdf_path: Path, timeout: int = 90) -> Path:
    """@page 크기를 그대로 지키는 실측 PDF를 만듭니다."""
    chrome = find_chrome()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--no-pdf-header-footer", "--virtual-time-budget=8000",
           f"--print-to-pdf={pdf_path}", str(html_path)]
    r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise SystemExit(f"PDF 생성 실패:\n{r.stderr.decode('utf-8', 'ignore')[-800:]}")
    return pdf_path


def html_to_png(html_path: Path, png_path: Path, width_px: int, height_px: int,
                timeout: int = 90) -> Path:
    """화면 캡처. 크롬은 창 최소 폭이 500px이므로 그보다 작게는 찍히지 않습니다."""
    chrome = find_chrome()
    png_path.parent.mkdir(parents=True, exist_ok=True)
    w = max(int(width_px), 500)
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
           f"--window-size={w},{int(height_px)}", "--virtual-time-budget=8000",
           f"--screenshot={png_path}", str(html_path)]
    subprocess.run(cmd, capture_output=True, timeout=timeout)
    if not png_path.exists():
        raise SystemExit("PNG 생성 실패")
    return png_path


def pdf_to_cmyk_image(pdf_path: Path, out_path: Path, dpi: int = 150,
                      quality: int = 95) -> Path | None:
    """인쇄용 CMYK 이미지.

    주의(경험담): Ghostscript의 pdfwrite CMYK 변환은 쓰지 않습니다.
    알파가 섞인 방사형 그라데이션이 딱딱한 경계로 깨집니다.
    RGB로 래스터라이즈한 뒤 ICC 프로파일로 변환합니다.
    """
    gs = find_ghostscript()
    if not gs:
        print("  ⚠ Ghostscript가 없어 CMYK 변환을 건너뜁니다 (PDF는 정상 생성됨)")
        return None
    try:
        from PIL import Image, ImageCms
    except ImportError:
        print("  ⚠ Pillow가 없어 CMYK 변환을 건너뜁니다  →  pip install pillow")
        return None

    Image.MAX_IMAGE_PIXELS = None
    with tempfile.TemporaryDirectory() as td:
        rgb_tif = Path(td) / "rgb.tif"
        subprocess.run([gs, "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=tiff24nc",
                        f"-r{dpi}", "-sCompression=lzw", "-dMaxBitmap=100000000",
                        f"-sOutputFile={rgb_tif}", str(pdf_path)],
                       capture_output=True, timeout=600)
        if not rgb_tif.exists():
            print("  ⚠ 래스터라이즈 실패 — CMYK 변환 건너뜀")
            return None
        src = Image.open(rgb_tif)
        icc = _cmyk_profile()
        if icc is None:
            print("  ⚠ CMYK 프로파일을 찾지 못해 RGB로 저장합니다")
            out = src.convert("RGB")
            icc_bytes = None
        else:
            srgb = ImageCms.createProfile("sRGB")
            out = ImageCms.profileToProfile(src, srgb, ImageCms.getOpenProfile(icc),
                                            outputMode="CMYK", renderingIntent=0)
            out = _fix_purple(out)
            icc_bytes = Path(icc).read_bytes()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        kw = {"dpi": (dpi, dpi)}
        if icc_bytes:
            kw["icc_profile"] = icc_bytes
        if out_path.suffix.lower() in (".jpg", ".jpeg"):
            out.save(out_path, quality=quality, optimize=True, **kw)
        else:
            out.save(out_path, **kw)
    return out_path


def _cmyk_profile() -> str | None:
    for c in ("/System/Library/ColorSync/Profiles/Generic CMYK Profile.icc",
              "/usr/share/color/icc/ISOcoated_v2_eci.icc",
              r"C:\Windows\System32\spool\drivers\color\RSWOP.icm",
              os.environ.get("CMYK_PROFILE", "")):
        if c and Path(c).exists():
            return c
    return None


def _fix_purple(img):
    """보라가 남색으로 빠지는 것을 막는 채널 교정.

    ICC 변환만 하면 C와 M 값이 비슷해져(차이 15 안팎) 보라가 남색으로 읽힙니다.
    진보라는 M이 C보다 30~40 높아야 합니다. C에서 M의 18%를 덜어냅니다.
    총 잉크량도 함께 내려갑니다.

    이 보정은 색을 직접 지정(brand.colors)했을 때도 똑같이 걸립니다.
    빨강·주황 계열은 C가 원래 낮아 거의 영향이 없고, 녹색·남색 계열은
    준비된 색 묶음(forest·navy)이 이미 같은 보정을 거쳐 검증된 값입니다.
    """
    try:
        import numpy as np
    except ImportError:
        return img
    a = np.asarray(img).astype(np.int16)
    a[:, :, 0] = np.clip(a[:, :, 0] - (0.18 * a[:, :, 1]).astype(np.int16), 0, 255)
    from PIL import Image
    return Image.fromarray(a.astype(np.uint8), "CMYK")


# ────────────────────────────── 도우미 ──────────────────────────────
def font_css(rel_prefix: str = "") -> str:
    """폰트를 상대경로로 연결하는 @font-face 묶음.

    폰트 파일을 결과물 폴더에 함께 복사하므로 다른 컴퓨터에서도 같게 보입니다.
    """
    weights = [("Medium", 500), ("SemiBold", 600), ("Bold", 700),
               ("ExtraBold", 800), ("Black", 900)]
    out = []
    for name, w in weights:
        out.append(
            f'@font-face{{font-family:"KitSans";font-weight:{w};'
            f'src:url("{rel_prefix}fonts/Pretendard-{name}.woff2") format("woff2");'
            f'font-display:block;}}')
    return "\n  ".join(out)


def copy_fonts(dest_dir: Path) -> None:
    d = dest_dir / "fonts"
    d.mkdir(parents=True, exist_ok=True)
    for f in (ASSETS / "fonts").glob("*"):
        shutil.copy2(f, d / f.name)


def mm(v) -> float:
    return float(v)


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def info(msg: str) -> None:
    print(f"  · {msg}")


def warn(msg: str) -> None:
    """멈추지는 않지만 결과물이 예상과 다를 수 있을 때 알립니다."""
    print(f"  ! {msg}")
