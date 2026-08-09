#!/usr/bin/env python3
"""Initialize and inspect a Viral View clone workflow without paid calls."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from viralview import ViralViewError, call_api, print_json, reject_credentials_in_payload  # noqa: E402


DEFAULT_STATE = ROOT / ".viralview" / "clone-workflow.json"


def write_state(path: Path, state: dict) -> None:
    reject_credentials_in_payload(state, "workflow state")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def command_start(args: argparse.Namespace) -> None:
    product = call_api("POST", "/api/ugc/scan-product", data={"productUrl": args.product_url}, timeout=120)
    library = call_api("GET", "/api/ugc/ad-library", query={
        "query": args.search_term,
        "style": args.style,
        "limit": args.limit,
    })
    state = {
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stage": "source-selection",
        "productUrl": args.product_url,
        "searchTerm": args.search_term,
        "style": args.style,
        "productScan": product,
        "librarySearch": library,
        "approvals": [],
    }
    write_state(Path(args.state), state)
    print_json(state)


def command_show(args: argparse.Namespace) -> None:
    path = Path(args.state)
    if not path.exists():
        raise ViralViewError(f"Workflow state does not exist: {path}")
    state = json.loads(path.read_text(encoding="utf-8"))
    reject_credentials_in_payload(state, "workflow state")
    print_json(state)


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage a local Viral View clone workflow state.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start")
    start.add_argument("--product-url", required=True)
    start.add_argument("--search-term", required=True)
    start.add_argument("--style", default="")
    start.add_argument("--limit", type=int, default=8)
    start.add_argument("--state", default=str(DEFAULT_STATE))
    start.set_defaults(func=command_start)

    show = subparsers.add_parser("show")
    show.add_argument("--state", default=str(DEFAULT_STATE))
    show.set_defaults(func=command_show)

    try:
        args = parser.parse_args()
        args.func(args)
        return 0
    except (ViralViewError, OSError, json.JSONDecodeError) as error:
        print_json({"success": False, "error": str(error)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
