#!/usr/bin/env python3
"""Scan a public product page through Viral View."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    return subprocess.run([
        sys.executable,
        str(ROOT / "scripts" / "viralview.py"),
        "scan-product",
        "--url",
        args.url,
    ], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
