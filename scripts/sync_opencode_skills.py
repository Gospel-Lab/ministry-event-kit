#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
오픈코드는 ~/.agents/skills/<name>/SKILL.md 를 훑어서 스킬을 찾는데,
심볼릭 링크는 따라가지 않는다(직접 확인함). 그래서 이 리포의 skills/*/SKILL.md 를
그 폴더에 실제 파일로 복사해 넣는다.

Claude Code·코덱스는 플러그인 전체(scripts/ 등)를 한 번에 설치하므로 SKILL.md
기준 두 단계 위에 scripts/ 가 있지만, 오픈코드는 스킬마다 별도 폴더라 그 구조가
없다. 그래서 scripts/·docs/·examples/ 도 SKILL.md 와 같은 폴더에 나란히 복사해
"PLUGIN_ROOT 찾는 법"(SKILL.md 참고)의 첫 번째 경로(같은 폴더)로 잡히게 한다.

event.yml 등 사용자의 작업 파일은 건드리지 않는다. skills/*/SKILL.md 나
scripts/·docs/·examples/ 를 고친 뒤 이 스크립트를 다시 돌리면 오픈코드 쪽도
최신 내용으로 맞춰진다.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
TARGET = Path.home() / ".agents" / "skills"
SHARED_DIRS = ["scripts", "docs", "examples", "assets", "templates"]


def main() -> None:
    if not SKILLS.is_dir():
        raise SystemExit(f"skills 폴더를 찾을 수 없습니다: {SKILLS}")

    for skill_dir in sorted(SKILLS.iterdir()):
        src = skill_dir / "SKILL.md"
        if not src.is_file():
            continue
        dest_dir = TARGET / f"event-kit-{skill_dir.name}"
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest_dir / "SKILL.md")
        for shared in SHARED_DIRS:
            shared_src = ROOT / shared
            if shared_src.is_dir():
                shutil.copytree(shared_src, dest_dir / shared, dirs_exist_ok=True)
        print(f"[OK] {dest_dir}")


if __name__ == "__main__":
    main()
