#!/usr/bin/env python3
"""Validate the public workspace without installing dependencies."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = [
    "clone-viral-ad",
    "search-library",
    "product-scan",
    "export-video",
    "character-options",
    "remix-script",
    "usage-costs",
]


def fail(message: str) -> None:
    raise RuntimeError(message)


def validate_skill(name: str) -> None:
    path = ROOT / "skills" / name / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\nname: ([a-z0-9-]+)\ndescription: (.+)\n---\n", text)
    if not match:
        fail(f"Invalid frontmatter: {path}")
    if match.group(1) != name:
        fail(f"Skill name mismatch: {path}")
    if len(match.group(2).strip()) < 50:
        fail(f"Skill description is too short: {path}")
    if "TODO" in text:
        fail(f"Unresolved TODO: {path}")
    if len(text.splitlines()) > 500:
        fail(f"Skill exceeds 500 lines: {path}")
    metadata = (ROOT / "skills" / name / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if "display_name:" not in metadata or f"$${name}" in metadata or f"${name}" not in metadata:
        fail(f"Invalid agent metadata: {path.parent / 'agents' / 'openai.yaml'}")
    for target in [".agents", ".claude", ".cursor"]:
        wrapper = ROOT / target / "skills" / name / "SKILL.md"
        if not wrapper.exists() or f"../../../skills/{name}/SKILL.md" not in wrapper.read_text(encoding="utf-8"):
            fail(f"Missing or stale skill entrypoint: {wrapper}")


def validate_python() -> None:
    for path in ROOT.rglob("*.py"):
        if ".git" in path.parts:
            continue
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def main() -> int:
    try:
        for name in SKILLS:
            validate_skill(name)
        json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        validate_python()

        shell_files = [str(path) for path in (ROOT / "scripts").glob("*.sh")]
        subprocess.run(["bash", "-n", *shell_files], check=True)
        subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=ROOT,
            check=True,
        )

        required_text = [
            ROOT / "AGENTS.md",
            ROOT / "CLAUDE.md",
            ROOT / "shared" / "spend-policy.md",
            ROOT / "skills" / "clone-viral-ad" / "SKILL.md",
            ROOT / "skills" / "character-options" / "SKILL.md",
        ]
        for path in required_text:
            text = path.read_text(encoding="utf-8").lower()
            if "explicit" not in text or "yes" not in text:
                fail(f"Spend confirmation language is missing: {path}")

        subprocess.run([sys.executable, str(ROOT / "scripts" / "check_secrets.py")], check=True)
        print("Workspace validation: PASS")
        return 0
    except (OSError, RuntimeError, SyntaxError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"Workspace validation: FAIL: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
