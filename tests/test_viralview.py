from __future__ import annotations

import json
import os
import sys
import argparse
import contextlib
import io
import threading
import tempfile
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import viralview  # noqa: E402


class ApiHandler(BaseHTTPRequestHandler):
    authorization = ""
    approval = ""
    requests: list[dict[str, object]] = []
    response_status = 200
    response_code = ""

    def do_GET(self) -> None:
        type(self).authorization = self.headers.get("Authorization", "")
        body = json.dumps({"success": True, "projects": []}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        type(self).authorization = self.headers.get("Authorization", "")
        type(self).approval = self.headers.get("X-ViralView-Approval", "")
        length = int(self.headers.get("Content-Length", "0"))
        request_body = self.rfile.read(length)
        decoded = json.loads(request_body) if request_body else {}
        type(self).requests.append({
            "path": self.path,
            "approval": type(self).approval,
            "body": decoded,
        })
        if self.path.endswith("/quote"):
            response = {
                "action": "frames",
                "model": "test-model",
                "items": [
                    {"id": "1", "model": "test-model", "durationSeconds": 3, "quality": "480p", "creditsEach": 12},
                    {"id": "2", "model": "test-model", "durationSeconds": 3, "quality": "480p", "creditsEach": 12},
                ],
                "creditsEach": 12,
                "creditsTotal": 24,
                "approvalToken": "temporary-approval-code",
                "expiresAt": "2030-01-01T00:00:00.000Z",
            }
            status = 200
        elif type(self).response_status >= 400:
            response = {"success": False, "code": type(self).response_code}
            status = type(self).response_status
        else:
            response = {"success": True}
            status = 200
        body = json.dumps(response).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class ViralViewClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.prior_api_key = os.environ.get("VIRALVIEW_API_KEY")
        self.prior_base_url = os.environ.get("VIRALVIEW_BASE_URL")
        self.prior_root = viralview.ROOT
        self.temp_root = tempfile.TemporaryDirectory()
        viralview.ROOT = Path(self.temp_root.name)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.key = "vv_live_" + ("0" * 32)
        os.environ["VIRALVIEW_API_KEY"] = self.key
        os.environ["VIRALVIEW_BASE_URL"] = f"http://127.0.0.1:{self.server.server_port}"
        ApiHandler.requests = []
        ApiHandler.response_status = 200
        ApiHandler.response_code = ""

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        if self.prior_api_key is None:
            os.environ.pop("VIRALVIEW_API_KEY", None)
        else:
            os.environ["VIRALVIEW_API_KEY"] = self.prior_api_key
        if self.prior_base_url is None:
            os.environ.pop("VIRALVIEW_BASE_URL", None)
        else:
            os.environ["VIRALVIEW_BASE_URL"] = self.prior_base_url
        viralview.ROOT = self.prior_root
        self.temp_root.cleanup()

    def test_bearer_header_is_sent_to_allowlisted_route(self) -> None:
        payload = viralview.call_api("GET", "/api/ugc/project")
        self.assertTrue(payload["success"])
        self.assertEqual(ApiHandler.authorization, f"Bearer {self.key}")

    def test_non_pipeline_route_is_blocked(self) -> None:
        with self.assertRaises(viralview.ViralViewError):
            viralview.call_api("GET", "/api/auth/session")

    def test_credential_fields_are_blocked(self) -> None:
        with self.assertRaises(viralview.ViralViewError):
            viralview.reject_credentials_in_payload({"kieApiKey": "not-allowed"})

    def test_redaction_removes_api_key_and_bearer_value(self) -> None:
        value = viralview.redact_string(f"key={self.key} Authorization: Bearer {self.key}")
        self.assertNotIn(self.key, value)
        self.assertIn("[REDACTED", value)

    def test_paid_generation_detection(self) -> None:
        self.assertTrue(viralview.paid_generation_request("POST", "/api/ugc/generate-overlay", {}))
        self.assertTrue(viralview.paid_generation_request(
            "POST", "/api/ugc/generate-kling", {"action": "generate"}
        ))
        self.assertFalse(viralview.paid_generation_request(
            "POST", "/api/ugc/generate-kling", {"action": "check"}
        ))
        self.assertTrue(viralview.paid_generation_request(
            "POST", "/api/v3/project/project_12345678/intent", {"type": "retry", "beat": "export"}
        ))
        self.assertFalse(viralview.paid_generation_request(
            "POST",
            "/api/ugc/stitch-videos",
            {"projectId": "project_12345678", "videoUrls": ["/api/uploads/scene.mp4"]},
        ))

    def test_v3_quote_actions_are_available_to_cli(self) -> None:
        for quote_action in ("product_cutout", "intent_retry"):
            args = viralview.build_parser().parse_args([
                "request", "POST", "/api/v3/project/project_12345678/intent",
                "--quote-only", "--quote-project-id", "project_12345678",
                "--quote-action", quote_action,
            ])
            self.assertEqual(args.quote_action, quote_action)
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                viralview.build_parser().parse_args([
                    "request", "POST", "/api/ugc/stitch-videos", "--quote-only",
                    "--quote-project-id", "project_12345678", "--quote-action", "export",
                ])

    def test_export_render_does_not_need_paid_approval(self) -> None:
        payload = {"projectId": "project_12345678", "videoUrls": ["/api/uploads/scene.mp4"]}
        args = argparse.Namespace(
            method="POST", path="/api/ugc/stitch-videos", data_file=None,
            data_json=json.dumps(payload), query=[], timeout=20,
            confirm_paid="NO", quote_only=False, quote_project_id="", quote_action=None,
            approval_token="",
        )
        with contextlib.redirect_stdout(io.StringIO()):
            viralview.command_request(args)
        self.assertEqual(len(ApiHandler.requests), 1)
        request = ApiHandler.requests[0]
        self.assertEqual(request["path"], "/api/ugc/stitch-videos")
        self.assertEqual(request["body"], payload)
        self.assertEqual(request["approval"], "")

    def test_paid_call_without_approval_is_refused_before_request(self) -> None:
        with self.assertRaisesRegex(viralview.ViralViewError, "approval token"):
            viralview.call_api(
                "POST",
                "/api/v3/project/project_12345678/frames",
                data={"action": "dispatch", "model": "test-model", "sceneNumbers": [1]},
            )
        self.assertEqual(ApiHandler.requests, [])

    def test_quote_then_dispatch_sends_same_payload_and_approval_header(self) -> None:
        payload = {
            "action": "dispatch",
            "requestId": "frame-request-7",
            "model": "test-model",
            "sceneNumbers": [1, 2],
            "useProductPhoto": True,
        }
        quote_args = argparse.Namespace(
            method="POST",
            path="/api/v3/project/project_12345678/frames",
            data_file=None,
            data_json=json.dumps(payload),
            query=[],
            timeout=20,
            confirm_paid="NO",
            quote_only=True,
            quote_project_id="project_12345678",
            quote_action="frames",
            approval_token="",
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            viralview.command_request(quote_args)
        quote_result = json.loads(output.getvalue())
        self.assertEqual(quote_result["estimatedCredits"], 24)
        self.assertEqual(quote_result["itemCount"], 2)
        self.assertEqual(quote_result["seconds"], 6)
        self.assertEqual(quote_result["approvalToken"], "temporary-approval-code")

        dispatch_args = argparse.Namespace(
            **{**vars(quote_args), "quote_only": False, "confirm_paid": "YES", "approval_token": quote_result["approvalToken"]}
        )
        with contextlib.redirect_stdout(io.StringIO()):
            viralview.command_request(dispatch_args)

        quote_request, dispatch_request = ApiHandler.requests
        self.assertTrue(quote_request["path"].endswith("/quote"))
        self.assertEqual(quote_request["body"], {"action": "frames", "payload": payload})
        self.assertEqual(dispatch_request["body"], payload)
        self.assertEqual(dispatch_request["approval"], "temporary-approval-code")

    def test_402_approval_code_maps_to_clear_error_and_audit_hides_tokens(self) -> None:
        ApiHandler.response_status = 402
        ApiHandler.response_code = "approval_expired"
        with self.assertRaises(viralview.ViralViewError) as caught:
            viralview.call_api(
                "POST",
                "/api/ugc/generate-kling",
                data={"action": "generate", "projectId": "project_12345678"},
                approval_token="temporary-approval-code",
            )
        self.assertIn("Approval expired - quote again and ask the user", str(caught.exception))
        self.assertNotIn("temporary-approval-code", str(caught.exception))
        audit = (viralview.ROOT / "logs" / "viralview-api.jsonl").read_text(encoding="utf-8")
        self.assertNotIn(self.key, audit)
        self.assertNotIn("temporary-approval-code", audit)


if __name__ == "__main__":
    unittest.main()
