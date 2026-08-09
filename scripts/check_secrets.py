#!/usr/bin/env python3
"""Fail when public files or Git history contain likely credentials."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".viralview", "__pycache__", ".venv", "venv", "logs", "references"}
SKIP_NAMES = {".env"}
PATTERNS = {
    "Viral View API key": re.compile(rb"vv_live_[0-9a-fA-F]{32}"),
    "GitHub token": re.compile(rb"gh[pousr]_[A-Za-z0-9_]{20,}"),
    "OpenAI-style key": re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    "Google API key": re.compile(rb"AIza[0-9A-Za-z_-]{20,}"),
    "AWS access key": re.compile(rb"(?:AKIA|ASIA)[0-9A-Z]{16}"),
    "Slack token": re.compile(rb"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "Private key": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "Bearer value": re.compile(rb"Authorization\s*:\s*Bearer\s+[A-Za-z0-9._~+/-]{12,}", re.IGNORECASE),
}
SENSITIVE_NAMES = re.compile(r"(^|/)(\.env|id_rsa|id_ed25519|credentials|secrets?)(\.|$)|\.(pem|p12|key)$", re.IGNORECASE)


def public_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if not path.is_file() or path.name in SKIP_NAMES or any(part in SKIP_PARTS for part in relative.parts):
            continue
        files.append(path)
    return files


def scan_bytes(label: str, data: bytes, findings: list[str]) -> None:
    for pattern_name, pattern in PATTERNS.items():
        if pattern.search(data):
            findings.append(f"{label}: {pattern_name}")


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in result.stdout.splitlines() if line]


def main() -> int:
    findings: list[str] = []
    for path in public_files():
        scan_bytes(str(path.relative_to(ROOT)), path.read_bytes(), findings)

    for name in tracked_files():
        if name != ".env.example" and SENSITIVE_NAMES.search(name):
            findings.append(f"{name}: sensitive filename is tracked")
        tracked_path = ROOT / name
        if tracked_path.is_file():
            scan_bytes(f"Tracked file {name}", tracked_path.read_bytes(), findings)

    history = subprocess.run(
        ["git", "log", "-p", "--all", "--no-ext-diff"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    scan_bytes("Git history", history.stdout, findings)

    for ignored_path in [".env", "MASTER_CONTEXT.md", "logs/viralview-api.jsonl", "references/private.png"]:
        ignored = subprocess.run(
            ["git", "check-ignore", "-q", ignored_path],
            cwd=ROOT,
            check=False,
        )
        if ignored.returncode != 0:
            findings.append(f"Required local path is not ignored: {ignored_path}")

    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        return 1
    print("Secret scan: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
