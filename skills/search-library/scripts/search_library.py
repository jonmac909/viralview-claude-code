#!/usr/bin/env python3
"""Search the Viral View ad library."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--style", default="")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--cursor", default="")
    args = parser.parse_args()
    command = [
        sys.executable,
        str(ROOT / "scripts" / "viralview.py"),
        "search-library",
        "--query",
        args.query,
        "--limit",
        str(args.limit),
    ]
    if args.style:
        command.extend(["--style", args.style])
    if args.cursor:
        command.extend(["--cursor", args.cursor])
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
