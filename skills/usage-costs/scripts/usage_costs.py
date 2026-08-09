#!/usr/bin/env python3
"""Summarize Viral View usage and calculate explicit batch estimates."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from viralview import ViralViewError, call_api, print_json  # noqa: E402


def local_summary() -> dict:
    path = ROOT / "logs" / "viralview-api.jsonl"
    if not path.exists():
        return {"requests": 0, "byPath": {}}
    counts: Counter[str] = Counter()
    total = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += 1
        counts[str(item.get("path", "unknown"))] += 1
    return {"requests": total, "byPath": dict(sorted(counts.items()))}


def command_recent(_: argparse.Namespace) -> None:
    usage = call_api("GET", "/api/ugc/usage")
    balance = call_api("GET", "/api/ugc/kie-balance")
    print_json({"success": True, "usage": usage, "balance": balance, "localAudit": local_summary()})


def command_forecast(args: argparse.Namespace) -> None:
    if args.count < 1 or args.credits_per_item <= 0:
        raise ViralViewError("Count and credits per item must be positive.")
    total = round(args.count * args.credits_per_item, 4)
    print_json({
        "success": True,
        "kind": args.kind,
        "model": args.model,
        "count": args.count,
        "creditsPerItem": args.credits_per_item,
        "estimatedCredits": total,
        "approvalRequired": True,
        "approvalText": "Ask the user for an explicit yes before submitting this exact batch.",
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    recent = subparsers.add_parser("recent")
    recent.set_defaults(func=command_recent)
    forecast = subparsers.add_parser("forecast")
    forecast.add_argument("--kind", choices=["image", "video"], required=True)
    forecast.add_argument("--model", required=True)
    forecast.add_argument("--count", type=int, required=True)
    forecast.add_argument("--credits-per-item", type=float, required=True)
    forecast.set_defaults(func=command_forecast)

    try:
        args = parser.parse_args()
        args.func(args)
        return 0
    except (ViralViewError, OSError) as error:
        print_json({"success": False, "error": str(error)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
