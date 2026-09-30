#!/usr/bin/env python3
"""Small, dependency-free client for the public Viral View API."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://app.viralview.io"
KEY_PATTERN = re.compile(r"^vv_live_[0-9a-f]{32}$")
KEY_VALUE_PATTERN = re.compile(r"vv_live_[0-9a-f]{8,}", re.IGNORECASE)
BEARER_PATTERN = re.compile(r"Bearer\s+[A-Za-z0-9._~+/-]+", re.IGNORECASE)
SENSITIVE_FIELD_PATTERN = re.compile(
    r"authorization|password|secret|token|api[_-]?key|apikey|kie[_-]?api[_-]?key|kieapikey",
    re.IGNORECASE,
)

ALLOWED_PATHS = {
    "/api/ugc/project",
    "/api/ugc/scan-product",
    "/api/ugc/extract-video",
    "/api/ugc/analyze-video",
    "/api/ugc/rewrite-script",
    "/api/ugc/generate-script",
    "/api/ugc/describe-character-frame",
    "/api/ugc/lock-character",
    "/api/ugc/prepare-character-identity-ref",
    "/api/ugc/generate-overlay",
    "/api/ugc/generate-kling",
    "/api/ugc/generate-veo",
    "/api/ugc/stitch-videos",
    "/api/ugc/ad-library",
    "/api/ugc/kie-balance",
    "/api/ugc/kie-status",
    "/api/ugc/redo-captions",
    "/api/ugc/usage",
    "/api/ugc/source-matches",
    "/api/ugc/meta-ad-library/search",
    "/api/v3/characters",
    "/api/upload",
    "/api/upload/multipart",
}
V3_PROJECT_SUFFIXES = {
    "quote",
    "intent",
    "context",
    "frames",
    "character-dispatch",
    "generate",
    "auto/start",
    "auto/stop",
    "auto/tick",
    "export-status",
    "product-cutout",
    "script-score",
    "ad-score",
    "enrich-supplied-source",
    "identity-product-qc",
    "lip-motion-qc",
}
V3_PROJECT_PATH_PATTERN = re.compile(
    r"^/api/v3/project/[A-Za-z0-9_-]{8,100}/(?P<suffix>[A-Za-z0-9/-]+)$"
)
APPROVAL_ERROR_MESSAGES = {
    "approval_required": "Approval required - quote this exact payload and ask the user before dispatch.",
    "approval_invalid": "Approval invalid - quote again and ask the user before dispatch.",
    "approval_expired": "Approval expired - quote again and ask the user.",
    "approval_replayed": "Approval already used - quote again and ask the user before retrying.",
    "over_daily_cap": "Daily credit cap reached - no paid request was accepted.",
}


class ViralViewError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status = status
        self.payload = payload


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip("\"").strip("'")
        if name and name not in os.environ:
            os.environ[name] = value


def redact_string(value: str) -> str:
    value = KEY_VALUE_PATTERN.sub("[REDACTED_API_KEY]", value)
    return BEARER_PATTERN.sub("Bearer [REDACTED]", value)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if SENSITIVE_FIELD_PATTERN.search(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return redact_string(value)
    return value


def reject_credentials_in_payload(value: Any, location: str = "payload") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if SENSITIVE_FIELD_PATTERN.search(key_text) and item not in (None, "", [], {}):
                raise ViralViewError(
                    f"Credential-like field '{key_text}' is not allowed in {location}. "
                    "Use VIRALVIEW_API_KEY in .env."
                )
            reject_credentials_in_payload(item, f"{location}.{key_text}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_credentials_in_payload(item, f"{location}[{index}]")
    elif isinstance(value, str) and (KEY_VALUE_PATTERN.search(value) or BEARER_PATTERN.search(value)):
        raise ViralViewError(f"Credential material is not allowed in {location}.")


def validate_path(path: str) -> str:
    parsed = urllib.parse.urlsplit(path)
    if parsed.scheme or parsed.netloc:
        raise ViralViewError("Pass an API path, not a full URL.")
    clean_path = parsed.path.rstrip("/") or "/"
    v3_match = V3_PROJECT_PATH_PATTERN.fullmatch(clean_path)
    allowed = (
        clean_path in ALLOWED_PATHS
        or clean_path.startswith("/api/ugc/ad-library/")
        or clean_path.startswith("/api/uploads/")
        or (v3_match is not None and v3_match.group("suffix") in V3_PROJECT_SUFFIXES)
    )
    if not allowed:
        raise ViralViewError(f"API path is not in the public pipeline allowlist: {clean_path}")
    return clean_path


def get_config() -> tuple[str, str]:
    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("VIRALVIEW_API_KEY", "").strip()
    if not KEY_PATTERN.fullmatch(api_key):
        raise ViralViewError(
            "VIRALVIEW_API_KEY is missing or malformed. Run ./scripts/setup.sh."
        )
    base_url = os.environ.get("VIRALVIEW_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    parsed = urllib.parse.urlsplit(base_url)
    is_local = parsed.hostname in {"127.0.0.1", "localhost"}
    if parsed.scheme != "https" and not (is_local and parsed.scheme == "http"):
        raise ViralViewError("VIRALVIEW_BASE_URL must use HTTPS, except for localhost testing.")
    return api_key, base_url


def parse_json_bytes(raw: bytes) -> Any:
    if not raw:
        return {}
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"success": False, "error": "Viral View returned a non-JSON response."}


def append_audit(method: str, path: str, status: int, elapsed_ms: int) -> None:
    log_dir = ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "method": method,
        "path": path,
        "status": status,
        "elapsedMs": elapsed_ms,
    }
    with (log_dir / "viralview-api.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, separators=(",", ":")) + "\n")


def call_api(
    method: str,
    path: str,
    *,
    query: dict[str, Any] | None = None,
    data: Any = None,
    approval_token: str | None = None,
    timeout: int = 60,
) -> Any:
    api_key, base_url = get_config()
    clean_path = validate_path(path)
    reject_credentials_in_payload(data)
    paid_call = paid_generation_request(method, clean_path, data)
    if paid_call and not approval_token:
        raise ViralViewError("Paid request blocked locally: an approval token from a matching quote is required.")
    if approval_token and not paid_call:
        raise ViralViewError("An approval token can only be sent with a paid generation request.")
    query_string = urllib.parse.urlencode(
        {key: value for key, value in (query or {}).items() if value not in (None, "")},
        doseq=True,
    )
    url = f"{base_url}{clean_path}"
    if query_string:
        url = f"{url}?{query_string}"

    body = None if data is None else json.dumps(data, separators=(",", ":")).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "viralview-agent-skills/1.0",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    if approval_token:
        if method.upper() != "POST":
            raise ViralViewError("Approval tokens are only allowed on paid POST requests.")
        headers["X-ViralView-Approval"] = approval_token

    request = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
    started = time.monotonic()
    status = 0
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            payload = parse_json_bytes(response.read())
    except urllib.error.HTTPError as error:
        status = error.code
        payload = parse_json_bytes(error.read())
        code = payload.get("code") if isinstance(payload, dict) else None
        message = APPROVAL_ERROR_MESSAGES.get(code) if isinstance(code, str) else None
        message = message or (payload.get("error") if isinstance(payload, dict) else None)
        message = str(message or f"Viral View returned HTTP {status}.")
        if approval_token:
            message = message.replace(approval_token, "[REDACTED_APPROVAL_TOKEN]")
        raise ViralViewError(redact_string(message), status, payload)
    except urllib.error.URLError as error:
        raise ViralViewError(f"Could not reach Viral View: {error.reason}") from error
    finally:
        elapsed_ms = round((time.monotonic() - started) * 1000)
        append_audit(method.upper(), clean_path, status, elapsed_ms)
    return payload


def load_json_argument(data_file: str | None, data_json: str | None) -> Any:
    if data_file and data_json:
        raise ViralViewError("Use either --data-file or --data-json, not both.")
    if data_file:
        return json.loads(Path(data_file).read_text(encoding="utf-8"))
    if data_json:
        return json.loads(data_json)
    return None


def paid_generation_request(method: str, path: str, data: Any) -> bool:
    if method.upper() != "POST":
        return False
    if path == "/api/ugc/generate-overlay":
        return True
    if path in {"/api/ugc/generate-kling", "/api/ugc/generate-veo"}:
        return not isinstance(data, dict) or data.get("action", "generate") == "generate"
    match = V3_PROJECT_PATH_PATTERN.fullmatch(path)
    if match:
        suffix = match.group("suffix")
        if suffix in {"character-dispatch", "auto/start"}:
            return True
        if suffix in {"frames", "generate"}:
            return isinstance(data, dict) and data.get("action") == "dispatch"
        if suffix == "product-cutout":
            return isinstance(data, dict) and data.get("action") in {"start", "start-fallback"}
        if suffix == "intent":
            return isinstance(data, dict) and data.get("type") == "retry" and data.get("beat") in {"character", "frames", "generate", "export"}
    if path == "/api/ugc/stitch-videos":
        return not isinstance(data, dict) or data.get("previewOnly") is not True
    return False


def print_json(value: Any) -> None:
    print(json.dumps(redact(value), indent=2, sort_keys=True))


def command_verify_key(_: argparse.Namespace) -> None:
    call_api("GET", "/api/ugc/project", timeout=20)
    print_json({"success": True, "authenticated": True})


def command_status(_: argparse.Namespace) -> None:
    print_json(call_api("GET", "/api/ugc/kie-status", timeout=20))


def command_projects(args: argparse.Namespace) -> None:
    print_json(call_api("GET", "/api/ugc/project", query={"id": args.id}))


def command_search_library(args: argparse.Namespace) -> None:
    print_json(call_api("GET", "/api/ugc/ad-library", query={
        "query": args.query,
        "style": args.style,
        "limit": args.limit,
        "cursor": args.cursor,
    }))


def command_library_item(args: argparse.Namespace) -> None:
    item_id = urllib.parse.quote(args.id, safe="")
    print_json(call_api("GET", f"/api/ugc/ad-library/{item_id}"))


def command_scan_product(args: argparse.Namespace) -> None:
    print_json(call_api("POST", "/api/ugc/scan-product", data={"productUrl": args.url}, timeout=120))


def command_usage(_: argparse.Namespace) -> None:
    print_json(call_api("GET", "/api/ugc/usage"))


def command_request(args: argparse.Namespace) -> None:
    path = validate_path(args.path)
    data = load_json_argument(args.data_file, args.data_json)
    paid = paid_generation_request(args.method, path, data)
    if args.quote_only and not paid:
        raise ViralViewError("--quote-only is only valid for a paid generation request.")
    if paid:
        if not isinstance(data, dict):
            raise ViralViewError("Paid requests need a JSON object so the same payload can be quoted and dispatched.")
        project_id_value = args.quote_project_id or data.get("projectId") or ""
        project_id = str(project_id_value).strip()
        if args.quote_only:
            if not project_id or not args.quote_action:
                raise ViralViewError("Quote-only needs --quote-project-id and --quote-action for the paid payload.")
            quote_path = f"/api/v3/project/{urllib.parse.quote(project_id, safe='')}/quote"
            quote = call_api("POST", quote_path, data={"action": args.quote_action, "payload": data}, timeout=args.timeout)
            print_quote(quote)
            return
        if args.confirm_paid != "YES":
            raise ViralViewError(
                "Paid image, video, or export request blocked locally. First run the same request with --quote-only, "
                "show the quote, and get an explicit user yes."
            )
        if not args.approval_token:
            raise ViralViewError("Paid request has no approval token. Quote this exact payload, ask the user, and pass --approval-token.")
        if not project_id or not args.quote_action:
            raise ViralViewError("Paid request needs --quote-project-id and --quote-action for a matching quote.")
    query = dict(item.split("=", 1) for item in (args.query or []))
    print_json(call_api(
        args.method, path, query=query, data=data,
        approval_token=args.approval_token if paid else None,
        timeout=args.timeout,
    ))


def print_quote(quote: Any) -> None:
    if not isinstance(quote, dict):
        raise ViralViewError("Viral View returned an invalid paid quote.")
    visible_fields = (
        "action", "model", "items", "creditsEach", "creditsTotal",
        "approvalToken", "expiresAt",
    )
    safe_quote = {field: quote[field] for field in visible_fields if field in quote}
    items = safe_quote.get("items")
    safe_quote["itemCount"] = len(items) if isinstance(items, list) else 0
    durations = [
        float(item["durationSeconds"])
        for item in items if isinstance(item, dict) and isinstance(item.get("durationSeconds"), (int, float))
    ] if isinstance(items, list) else []
    safe_quote["seconds"] = sum(durations)
    safe_quote["estimatedCredits"] = quote.get("creditsTotal")
    print(json.dumps(safe_quote, indent=2, sort_keys=True))


def command_poll_get(args: argparse.Namespace) -> None:
    deadline = time.monotonic() + args.timeout
    while True:
        payload = call_api("GET", args.path, query={args.job_parameter: args.job_id}, timeout=60)
        status = str(payload.get("status", "")).lower() if isinstance(payload, dict) else ""
        if status in {"done", "success", "completed"} or (
            isinstance(payload, dict) and (payload.get("done") is True or payload.get("videoUrl"))
        ):
            print_json(payload)
            return
        if status in {"failed", "error", "cancelled"}:
            raise ViralViewError("Viral View job failed.", payload=payload)
        if time.monotonic() >= deadline:
            raise ViralViewError(f"Timed out after {args.timeout} seconds while polling {args.path}.")
        time.sleep(args.interval)


def command_poll_video(args: argparse.Namespace) -> None:
    deadline = time.monotonic() + args.timeout
    while True:
        payload = call_api("POST", "/api/ugc/generate-kling", data={
            "action": "check",
            "taskId": args.task_id,
        }, timeout=60)
        if isinstance(payload, dict) and (payload.get("done") is True or payload.get("videos")):
            print_json(payload)
            return
        if isinstance(payload, dict) and payload.get("success") is False and payload.get("error"):
            raise ViralViewError("Video generation failed.", payload=payload)
        if time.monotonic() >= deadline:
            raise ViralViewError(f"Timed out after {args.timeout} seconds while polling video generation.")
        time.sleep(args.interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Call the public Viral View API without extra packages.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify-key", help="Verify bearer authentication without exposing the key.")
    verify.set_defaults(func=command_verify_key)

    status = subparsers.add_parser("status", help="Check Viral View generation service health.")
    status.set_defaults(func=command_status)

    projects = subparsers.add_parser("projects", help="List projects or load one project.")
    projects.add_argument("--id")
    projects.set_defaults(func=command_projects)

    search = subparsers.add_parser("search-library", help="Search the Viral View ad library.")
    search.add_argument("--query", default="")
    search.add_argument("--style", default="")
    search.add_argument("--limit", type=int, default=12)
    search.add_argument("--cursor", default="")
    search.set_defaults(func=command_search_library)

    item = subparsers.add_parser("library-item", help="Load one ad library item.")
    item.add_argument("--id", required=True)
    item.set_defaults(func=command_library_item)

    scan = subparsers.add_parser("scan-product", help="Extract editable product details from a URL.")
    scan.add_argument("--url", required=True)
    scan.set_defaults(func=command_scan_product)

    usage = subparsers.add_parser("usage", help="Read recent API usage events.")
    usage.set_defaults(func=command_usage)

    request = subparsers.add_parser("request", help="Call an allowlisted public pipeline endpoint.")
    request.add_argument("method", choices=["GET", "POST", "DELETE"])
    request.add_argument("path")
    request.add_argument("--query", action="append", help="Query parameter in key=value form.")
    request.add_argument("--data-file")
    request.add_argument("--data-json")
    request.add_argument("--timeout", type=int, default=120)
    request.add_argument("--confirm-paid", default="NO", choices=["NO", "YES"])
    request.add_argument("--quote-only", action="store_true", help="Quote a paid payload without dispatching it.")
    request.add_argument("--quote-project-id", default="", help="Project ID for the V3 paid quote route.")
    request.add_argument(
        "--quote-action",
        choices=[
            "characters", "frames", "frame_remake", "scene_videos", "scene_regenerate",
            "lip_redo", "auto", "overlay", "export", "product_cutout", "intent_retry",
        ],
    )
    request.add_argument("--approval-token", default="", help="Short-lived quote token sent only in X-ViralView-Approval.")
    request.set_defaults(func=command_request)

    poll_get = subparsers.add_parser("poll-get", help="Poll a GET job endpoint until it completes.")
    poll_get.add_argument("path")
    poll_get.add_argument("--job-id", required=True)
    poll_get.add_argument("--job-parameter", default="jobId")
    poll_get.add_argument("--interval", type=int, default=5)
    poll_get.add_argument("--timeout", type=int, default=1800)
    poll_get.set_defaults(func=command_poll_get)

    poll_video = subparsers.add_parser("poll-video", help="Poll a Viral View video task until it completes.")
    poll_video.add_argument("--task-id", required=True)
    poll_video.add_argument("--interval", type=int, default=8)
    poll_video.add_argument("--timeout", type=int, default=1800)
    poll_video.set_defaults(func=command_poll_video)
    return parser


def main() -> int:
    try:
        args = build_parser().parse_args()
        args.func(args)
        return 0
    except (ViralViewError, json.JSONDecodeError, OSError) as error:
        payload = getattr(error, "payload", None)
        output = {"success": False, "error": str(error)}
        if isinstance(payload, dict) and payload.get("code"):
            output["code"] = payload["code"]
        print_json(output)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
