from __future__ import annotations

import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import viralview  # noqa: E402


class ApiHandler(BaseHTTPRequestHandler):
    authorization = ""

    def do_GET(self) -> None:
        type(self).authorization = self.headers.get("Authorization", "")
        body = json.dumps({"success": True, "projects": []}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class ViralViewClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.key = "vv_live_" + ("0" * 32)
        os.environ["VIRALVIEW_API_KEY"] = self.key
        os.environ["VIRALVIEW_BASE_URL"] = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        os.environ.pop("VIRALVIEW_API_KEY", None)
        os.environ.pop("VIRALVIEW_BASE_URL", None)

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


if __name__ == "__main__":
    unittest.main()
