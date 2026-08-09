#!/usr/bin/env python3
"""Expose canonical skills to Codex, Claude Code, and Cursor."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = [ROOT / ".agents" / "skills", ROOT / ".claude" / "skills", ROOT / ".cursor" / "skills"]


def main() -> int:
    for skill_file in sorted((ROOT / "skills").glob("*/SKILL.md")):
        text = skill_file.read_text(encoding="utf-8")
        match = re.match(r"^---\nname: ([a-z0-9-]+)\ndescription: (.+)\n---\n", text)
        if not match:
            raise RuntimeError(f"Invalid canonical skill frontmatter: {skill_file}")
        name, description = match.groups()
        wrapper = (
            "---\n"
            f"name: {name}\n"
            f"description: {description}\n"
            "---\n\n"
            f"# {name}\n\n"
            f"Read `../../../skills/{name}/SKILL.md` completely and follow it as the canonical skill.\n"
        )
        for target_root in TARGETS:
            target = target_root / name / "SKILL.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(wrapper, encoding="utf-8")
    print("Skill entrypoints synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
