#!/usr/bin/env python3
"""Check scene speaking pace and submit a script rewrite."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from viralview import ViralViewError, call_api, print_json  # noqa: E402


def word_count(value: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", value))


def timing_report(payload: dict) -> list[dict]:
    dialogue_map = payload.get("sceneDialogues", {})
    rows = []
    for scene in payload.get("scenes", []):
        number = scene.get("number")
        dialogue = str(dialogue_map.get(str(number), dialogue_map.get(number, scene.get("dialogue", "")))).strip()
        start = float(scene.get("startTime", 0) or 0)
        end = float(scene.get("endTime", 0) or 0)
        duration = float(scene.get("durationSeconds", 0) or 0) or max(0.0, end - start)
        words = word_count(dialogue)
        wps = round(words / duration, 2) if duration > 0 else None
        status = "unknown"
        if wps is not None:
            status = "too_short" if wps < 3.2 else "too_long" if wps > 4.4 else "fits"
        rows.append({
            "scene": number,
            "durationSeconds": duration,
            "words": words,
            "wordsPerSecond": wps,
            "status": status,
            "dialogue": dialogue,
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["check", "rewrite"])
    parser.add_argument("--payload", required=True)
    args = parser.parse_args()
    try:
        payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ViralViewError("Rewrite payload must be a JSON object.")
        if args.command == "check":
            print_json({"success": True, "scenes": timing_report(payload)})
        else:
            response = call_api("POST", "/api/ugc/rewrite-script", data=payload, timeout=180)
            print_json({"success": True, "response": response, "inputTiming": timing_report(payload)})
        return 0
    except (ViralViewError, OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        print_json({"success": False, "error": str(error)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
