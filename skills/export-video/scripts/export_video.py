#!/usr/bin/env python3
"""Retrieve or create a Viral View final export."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from viralview import ViralViewError, call_api, print_json  # noqa: E402


def command_fetch(args: argparse.Namespace) -> None:
    payload = call_api("GET", "/api/ugc/project", query={"id": args.project_id})
    project = payload.get("project", {}) if isinstance(payload, dict) else {}
    video_url = project.get("stitched_video_url") if isinstance(project, dict) else None
    print_json({
        "success": bool(video_url),
        "projectId": args.project_id,
        "videoUrl": video_url,
        "status": "ready" if video_url else "not_exported",
    })


def command_export(args: argparse.Namespace) -> None:
    if args.confirm_export != "YES":
        raise ViralViewError("Export blocked. Review the approved scene payload, then pass --confirm-export YES.")
    data = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    response = call_api("POST", "/api/ugc/stitch-videos", data=data, timeout=180)
    if not isinstance(response, dict):
        raise ViralViewError("Export returned an invalid response.")
    if response.get("videoUrl"):
        print_json(response)
        return
    job_id = response.get("jobId")
    if not job_id:
        raise ViralViewError("Export did not return a video URL or job ID.", payload=response)

    deadline = time.monotonic() + args.timeout
    while time.monotonic() < deadline:
        status = call_api("GET", "/api/ugc/stitch-videos", query={"jobId": job_id}, timeout=180)
        state = str(status.get("status", "")).lower() if isinstance(status, dict) else ""
        if isinstance(status, dict) and status.get("videoUrl"):
            print_json(status)
            return
        if state in {"failed", "error", "cancelled"}:
            raise ViralViewError("Export failed.", payload=status)
        time.sleep(args.interval)
    raise ViralViewError(f"Export polling timed out after {args.timeout} seconds. Resume job {job_id}.")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    fetch = subparsers.add_parser("fetch")
    fetch.add_argument("--project-id", required=True)
    fetch.set_defaults(func=command_fetch)

    export = subparsers.add_parser("export")
    export.add_argument("--payload", required=True)
    export.add_argument("--confirm-export", choices=["NO", "YES"], default="NO")
    export.add_argument("--interval", type=int, default=3)
    export.add_argument("--timeout", type=int, default=1800)
    export.set_defaults(func=command_export)

    try:
        args = parser.parse_args()
        args.func(args)
        return 0
    except (ViralViewError, OSError, json.JSONDecodeError) as error:
        print_json({"success": False, "error": str(error)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
