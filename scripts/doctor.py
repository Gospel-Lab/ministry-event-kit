#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
내 컴퓨터 점검 — ministry-event-kit

  python scripts/doctor.py

무엇이 있고 무엇이 없는지, 없으면 어떻게 설치하는지 알려줍니다.
처음 쓰기 전에 한 번 돌려보세요.

※ 이 파일만은 특수문자를 쓰지 않습니다.
   점검 도구가 점검 대상인 인코딩 문제로 죽으면 아무것도 알 수 없습니다.
   [OK] [--] [!!] 로만 표시합니다.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

WIN = os.name == "nt"
ROOT = Path(__file__).resolve().parent.parent

rows: list[tuple[str, str, str, str]] = []   # (표시, 항목, 상태, 안내)
missing_required = 0
missing_optional = 0


def add(ok: bool, required: bool, name: str, detail: str, howto: str = "") -> None:
    global missing_required, missing_optional
    if ok:
        mark = "[OK]"
    elif required:
        mark = "[!!]"
        missing_required += 1
    else:
        mark = "[--]"
        missing_optional += 1
    rows.append((mark, name, detail, "" if ok else howto))


def main() -> int:
    print("=" * 62)
    print(" ministry-event-kit  environment check")
    print("=" * 62)

    # 1. 파이썬
    v = sys.version_info
    add(v >= (3, 9), True, "Python",
        f"{v.major}.{v.minor}.{v.micro}",
        "Python 3.9 or newer: https://www.python.org/downloads/")

    # 2. 콘솔 인코딩 - 윈도우에서 가장 흔한 사고 지점
    enc = (getattr(sys.stdout, "encoding", "") or "?").lower()
    utf8 = "utf" in enc
    add(True, False, "Console encoding", enc,
        "")
    if WIN and not utf8:
        print("  note: console is not UTF-8. The kit forces UTF-8 output itself,")
        print("        but if Korean text still breaks, run:  chcp 65001")

    # 3. 크롬 - 필수
    chrome = ""
    try:
        from kit import find_chrome
        chrome = find_chrome()
    except SystemExit:
        chrome = ""
    except Exception as e:                       # noqa: BLE001
        chrome = ""
        print(f"  note: chrome lookup failed: {e}")
    add(bool(chrome), True, "Chrome / Edge",
        (chrome[:52] + "...") if len(chrome) > 55 else (chrome or "not found"),
        "Install Chrome (https://google.com/chrome). On Windows, Edge also works. "
        "Or set CHROME_PATH.")

    # 4. 고스트스크립트 - 선택 (CMYK 이미지)
    gs = None
    try:
        from kit import find_ghostscript
        gs = find_ghostscript()
    except Exception:                            # noqa: BLE001
        gs = None
    add(bool(gs), False, "Ghostscript",
        (gs or "not found") if not gs else Path(gs).name,
        "Windows: winget install ArtifexSoftware.GhostScript | "
        "Mac: brew install ghostscript  (without it: PDF is fine, CMYK image is skipped)")

    # 5. Pillow / numpy - 선택 (CMYK 색 보정)
    for mod, why in (("PIL", "CMYK conversion"), ("numpy", "CMYK color fix")):
        try:
            __import__(mod)
            add(True, False, mod if mod != "PIL" else "Pillow", "installed")
        except ImportError:
            add(False, False, mod if mod != "PIL" else "Pillow", "not installed",
                f"{'py -m pip' if WIN else 'pip3'} install pillow numpy   ({why})")

    # 6. QR - 선택 (포스터)
    qr = None
    for mod in ("segno", "qrcode"):
        try:
            __import__(mod)
            qr = mod
            break
        except ImportError:
            continue
    add(bool(qr), False, "QR code", qr or "not installed",
        f"{'py -m pip' if WIN else 'pip3'} install segno   "
        "(without it: the poster shows the address as text instead of a QR code)")

    # 7. PyYAML - 선택 (없어도 내장 파서로 동작)
    try:
        import yaml            # noqa: F401
        add(True, False, "PyYAML", "installed")
    except ImportError:
        add(True, False, "PyYAML", "not installed (built-in parser will be used)")

    # 8. 폰트
    fonts = sorted((ROOT / "assets" / "fonts").glob("*.woff2"))
    add(len(fonts) >= 5, True, "Fonts", f"{len(fonts)} files",
        "The assets/fonts folder is incomplete. Download the kit again.")

    # 9. 쓰기 권한
    try:
        probe = Path.cwd() / ".event_kit_write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        writable = True
    except OSError:
        writable = False
    add(writable, True, "Write access", str(Path.cwd())[:52],
        "Cannot write in this folder. Move to your Documents folder and try again.")

    # 10. 한글 폴더 경로 경고 (윈도우에서 간혹 문제)
    if WIN and any(ord(c) > 127 for c in str(ROOT)):
        print("  note: the kit is installed under a path containing non-ASCII")
        print("        characters. If anything fails oddly, try a plain-ASCII path.")

    # ── 출력 ──
    print()
    w = max(len(r[1]) for r in rows)
    for mark, name, detail, howto in rows:
        print(f" {mark} {name.ljust(w)}  {detail}")
        if howto:
            print(f"      -> {howto}")
    print()

    if missing_required:
        print(f" {missing_required} required item(s) missing. "
              f"The kit will not run until these are installed.")
        return 1
    if missing_optional:
        print(f" All required items OK. {missing_optional} optional item(s) missing")
        print(" (the kit runs; some outputs are skipped or simplified).")
        return 0
    print(" Everything is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
