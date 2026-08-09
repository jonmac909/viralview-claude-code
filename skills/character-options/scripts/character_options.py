#!/usr/bin/env python3
"""Prepare and generate a three-option Viral View character batch."""

from __future__ import annotations

import argparse
import sys
import time
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from viralview import ViralViewError, call_api, print_json  # noqa: E402


MODELS = [
    ("nano-banana-pro", "Option 1: create a distinct fictional adult identity while preserving the approved casting, framing, and setting."),
    ("seedream/5-pro-text-to-image", "Option 2: create a second distinct fictional adult identity with different facial geometry and styling."),
    ("gpt-image-2-text-to-image", "Option 3: create a third distinct fictional adult identity with different hair and facial geometry."),
]


def command_prepare(args: argparse.Namespace) -> None:
    print_json(call_api("POST", "/api/ugc/describe-character-frame", data={
        "imageUrl": args.image_url,
        "variationHint": args.variation_hint,
    }, timeout=120))


def command_generate(args: argparse.Namespace) -> None:
    if args.confirm != "yes":
        raise ViralViewError("Paid character generation is blocked until the user explicitly replies yes.")
    if args.estimated_credits <= 0:
        raise ViralViewError("A positive total credit estimate is required before character generation.")
    base_prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    if not base_prompt:
        raise ViralViewError("Character prompt file is empty.")

    jobs = []
    for model, variation in MODELS:
        response = call_api("POST", "/api/ugc/generate-overlay", data={
            "prompt": f"{base_prompt} {variation} Return one vertical 9:16 image with no text, logo, or watermark.",
            "aspectRatio": "9:16",
            "model": model,
            "referenceImageUrls": [],
            "requestId": f"agent-character-{uuid.uuid4().hex}",
        }, timeout=120)
        task_id = response.get("taskId") if isinstance(response, dict) else None
        if not task_id:
            raise ViralViewError(f"Character generation did not return a task ID for {model}.", payload=response)
        jobs.append({"model": model, "taskId": task_id, "status": "active"})

    deadline = time.monotonic() + args.timeout
    while any(job["status"] == "active" for job in jobs) and time.monotonic() < deadline:
        for job in jobs:
            if job["status"] != "active":
                continue
            payload = call_api("GET", "/api/ugc/generate-overlay", query={"taskId": job["taskId"]}, timeout=60)
            status = str(payload.get("status", "")).lower() if isinstance(payload, dict) else ""
            if isinstance(payload, dict) and payload.get("imageUrl"):
                job.update({"status": "success", "imageUrl": payload["imageUrl"]})
            elif status in {"failed", "error", "cancelled", "unchanged"}:
                job.update({"status": "failed", "error": "Character option failed."})
        if any(job["status"] == "active" for job in jobs):
            time.sleep(args.interval)

    for job in jobs:
        if job["status"] == "active":
            job["status"] = "timeout"
    print_json({
        "success": any(job["status"] == "success" for job in jobs),
        "estimatedCredits": args.estimated_credits,
        "options": jobs,
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--image-url", required=True)
    prepare.add_argument("--variation-hint", default="")
    prepare.set_defaults(func=command_prepare)

    generate = subparsers.add_parser("generate")
    generate.add_argument("--prompt-file", required=True)
    generate.add_argument("--estimated-credits", type=float, required=True)
    generate.add_argument("--confirm", choices=["no", "yes"], default="no")
    generate.add_argument("--interval", type=int, default=5)
    generate.add_argument("--timeout", type=int, default=1800)
    generate.set_defaults(func=command_generate)

    try:
        args = parser.parse_args()
        args.func(args)
        return 0
    except (ViralViewError, OSError) as error:
        print_json({"success": False, "error": str(error)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
