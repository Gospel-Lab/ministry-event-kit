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


# ────────────────────────────── 콘솔 인코딩 ──────────────────────────────
# 윈도우 명령 프롬프트는 한글 코드페이지(cp949)를 씁니다. 진행 표시에 쓰는
# ✓ · ! 같은 문자가 cp949 에 없어서, 그냥 두면 첫 줄을 찍다가 UnicodeEncodeError
# 로 죽습니다. 파이썬 3.15 부터는 UTF-8 이 기본이지만(PEP 686) 그 이전 버전을
# 쓰는 컴퓨터가 훨씬 많습니다.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass          # 구버전이거나 파이프로 연결된 경우 — 그대로 둡니다


# ────────────────────────────── 크롬 찾기 ──────────────────────────────
def _win_chrome_candidates() -> list[str]:
    """윈도우 설치 위치. 사용자 계정 설치와 엣지까지 포함합니다.

    엣지를 넣는 이유: 윈도우에는 엣지가 반드시 깔려 있고 크롬과 같은 엔진이라
    그대로 씁니다. 크롬을 따로 설치하지 않은 교회 컴퓨터의 실질적인 대안입니다.
    엣지는 PATH 에 등록되지 않으므로 절대경로로 찾아야 합니다.
    """
    out = []
    for var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        base = os.environ.get(var)
        if not base:
            continue
        out += [
            str(Path(base) / "Google/Chrome/Application/chrome.exe"),
            str(Path(base) / "Microsoft/Edge/Application/msedge.exe"),
            str(Path(base) / "Chromium/Application/chrome.exe"),
        ]
    return out


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
    for c in CHROME_CANDIDATES + _win_chrome_candidates():
        if c and Path(c).exists():
            return c
    for name in ("google-chrome", "chromium", "chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    raise SystemExit(
        "크롬을 찾지 못했습니다.\n"
        "  · 크롬을 설치하세요 (https://google.com/chrome)\n"
        "  · 윈도우라면 엣지(Edge)도 그대로 쓸 수 있습니다. 보통 이미 깔려 있습니다\n"
        "  · 이미 있다면 CHROME_PATH 환경변수로 실행 파일 경로를 알려주세요\n"
        "  · 무엇이 없는지 한 번에 보려면: python scripts/doctor.py"
    )


def find_ghostscript() -> str | None:
    for name in ("gs", "gswin64c", "gswin32c"):
        p = shutil.which(name)
        if p:
            return p
    for c in ("/opt/homebrew/bin/gs", "/usr/local/bin/gs"):
        if Path(c).exists():
            return c
    # 윈도우: winget 으로 막 설치하면 PATH 반영 전이라 which 가 실패합니다
    for var in ("PROGRAMFILES", "PROGRAMFILES(X86)"):
        base = os.environ.get(var)
        if not base:
            continue
        for exe in sorted(Path(base).glob("gs/gs*/bin/gswin*c.exe"), reverse=True):
            return str(exe)
    return None


def pdf_page_size_mm(pdf: Path) -> tuple[float, float] | None:
    """PDF 첫 쪽의 실제 크기(mm). pdfinfo 가 없는 윈도우에서도 확인할 수 있게
    /MediaBox 를 직접 읽습니다. 1pt = 1/72인치."""
    try:
        head = pdf.read_bytes()[:400_000]
    except OSError:
        return None
    m = re.search(rb"/MediaBox\s*\[\s*([\d.+-]+)\s+([\d.+-]+)\s+([\d.+-]+)\s+([\d.+-]+)", head)
    if not m:
        return None
    x0, y0, x1, y1 = (float(v) for v in m.groups())
    return (abs(x1 - x0) / 72 * MM_PER_IN, abs(y1 - y0) / 72 * MM_PER_IN)


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
    if not p.exists():
        raise SystemExit(
            f"{p} 파일이 없습니다.\n"
            f"  · 행사 정보 파일을 먼저 만드세요 (/event-kit:setup)\n"
            f"  · 파일이 다른 폴더에 있다면 --event 뒤에 그 경로를 적어 주세요")
    raw = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        return json.loads(raw)
    try:
        import yaml  # type: ignore
    except ImportError:
        return _mini_yaml(raw)
    try:
        return yaml.safe_load(raw) or {}
    except yaml.YAMLError as e:                  # noqa: PERF203
        raise SystemExit(_yaml_help(p, raw, e)) from None


def _yaml_help(path: Path, raw: str, err) -> str:
    """문법 오류를 사람이 고칠 수 있는 말로 바꿉니다.

    그냥 두면 파이썬 추적(traceback) 20줄이 그대로 뜹니다.
    디자인 도구도 못 다루는 분이 쓰는 도구에서 그것은 막다른 길입니다.
    """
    mark = getattr(err, "problem_mark", None)
    out = [f"{path.name} 을 읽지 못했습니다 — 문법이 맞지 않습니다.", ""]
    if mark is not None:
        lines = raw.splitlines()
        n = mark.line                            # 0부터 셉니다
        for i in range(max(0, n - 1), min(len(lines), n + 2)):
            head = "→" if i == n else " "
            out.append(f"  {head} {i + 1:>3} | {lines[i]}")
        out.append(f"        {' ' * (mark.column + 4)}^  이 부근")
    out += [
        "",
        "자주 나오는 원인",
        '  · 값에 : 나 # 나 따옴표가 들어 있으면 값 전체를 "큰따옴표"로 감싸세요',
        '        title: "특별새벽기도: 다시 시작"',
        "  · 들여쓰기는 공백으로만 합니다. 탭(Tab)은 오류가 납니다",
        "  · 목록은 - 뒤에 공백을 한 칸 둡니다",
    ]
    return "\n".join(out)


def _strip_comment(s: str) -> str:
    """줄 끝 주석을 떼되 따옴표 안은 건드리지 않습니다.

    색을 "#0a2f3a" 처럼 적으면 값 안에 #이 들어갑니다. 단순히 #에서 자르면
    색이 통째로 날아갑니다. YAML 규칙대로 '공백 뒤의 #'만 주석으로 봅니다.
    """
    out: list[str] = []
    quote = ""
    for ch in s:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#" and (not out or out[-1] in " \t"):
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _split_flow(s: str) -> list[str]:
    """{a: 1, b: 2} 안쪽을 쉼표로 나눕니다. 따옴표·중괄호 안의 쉼표는 셈하지 않습니다."""
    parts, buf, depth, quote = [], [], 0, ""
    for ch in s:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in "\"'":
            quote = ch
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    if "".join(buf).strip():
        parts.append("".join(buf))
    return parts


def _mini_yaml(raw: str) -> dict:
    root: dict = {}
    stack = [(-1, root)]
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        line_s = _strip_comment(line.strip())
        if not line_s:
            continue
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
    v = v.strip()
    # 한 줄로 적은 형태 — banner: {width_mm: 4000, height_mm: 900}
    if v.startswith("{") and v.endswith("}"):
        out: dict = {}
        for part in _split_flow(v[1:-1]):
            k, sep, val = part.partition(":")
            if sep:
                out[k.strip()] = _scalar(val)
        return out
    if v.startswith("[") and v.endswith("]"):
        return [_scalar(x) for x in _split_flow(v[1:-1])]
    v = v.strip('"').strip("'")
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def _fix_lists(raw: str, tree: dict) -> dict:
    """_mini_yaml 보조 — '키:' 다음 줄이 '- '면 목록으로 만든다."""
    lines = [l[:len(l) - len(l.lstrip())] + _strip_comment(l.strip())
             for l in raw.splitlines()
             if l.strip() and not l.lstrip().startswith("#")]
    lines = [l for l in lines if l.strip()]
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
def html_to_pdf(html_path: Path, pdf_path: Path, timeout: int | None = None,
                pages: int = 1) -> Path:
    """@page 크기를 그대로 지키는 실측 PDF를 만듭니다.

    pages 는 예상 쪽수입니다. 시간은 파일 크기가 아니라 쪽수를 따라갑니다 —
    명찰 500명(500쪽)은 실측 2분이 걸려서, 고정 90초로는 500명 행사에서
    반드시 실패합니다. 쪽수에 맞춰 기다리는 시간을 늘립니다.
    """
    if timeout is None:
        timeout = max(90, int(40 + pages * 1.8))
    chrome = find_chrome()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--no-pdf-header-footer", "--virtual-time-budget=8000",
           f"--print-to-pdf={pdf_path}", str(html_path)]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise SystemExit(
            f"PDF 를 만드는 데 {timeout}초를 넘겼습니다 ({pages}쪽).\n"
            f"  · 인원이나 항목을 나눠서 두 번에 만들어 보세요\n"
            f"  · 다른 무거운 프로그램을 닫으면 빨라집니다") from None
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
