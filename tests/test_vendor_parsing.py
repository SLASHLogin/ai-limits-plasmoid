#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 SLASHLogin
# SPDX-License-Identifier: GPL-3.0-or-later
"""Parse recorded vendor responses without contacting any vendor.

test_helper.py covers the signed-out and configuration paths. This file covers
the part that only ran against a live account before: turning a real provider
payload into the windows the applet draws. The fixtures in tests/fixtures/ are
hand-written in the shape each endpoint returns, with invented numbers and no
credentials of any kind.
"""

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = Path(os.environ.get(
    "LIMIT_WIDGET_HELPER", ROOT / "package/contents/tools/limit-widget-helper"))
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_helper():
    """Import the collector as a module so its functions can be called."""
    loader = importlib.machinery.SourceFileLoader("limit_widget_helper", str(HELPER))
    spec = importlib.util.spec_from_loader("limit_widget_helper", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class VendorParsingTest(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()

    def windows_by_label(self, record):
        return {w["label"]: w for w in record["windows"]}

    # --- Codex -----------------------------------------------------------

    def test_codex_payload_becomes_percent_windows(self):
        h = self.helper
        h.http_json = lambda *a, **k: (fixture("codex-usage.json"), {}, 200, None)
        h.codex_auth_path = lambda: self._codex_auth()

        record = h.codex_source()
        self.assertEqual(record["state"], "ok")
        windows = self.windows_by_label(record)

        # 42.5% used must be reported as remaining, not as used.
        self.assertAlmostEqual(windows["5h"]["remaining"], 57.5)
        self.assertAlmostEqual(windows["5h"]["used"], 42.5)
        self.assertEqual(windows["5h"]["unit"], "percent")
        self.assertAlmostEqual(windows["7d"]["remaining"], 88.0)

    def test_codex_model_specific_window_is_kept(self):
        """A model cap must not disappear behind the combined window."""
        h = self.helper
        h.http_json = lambda *a, **k: (fixture("codex-usage.json"), {}, 200, None)
        h.codex_auth_path = lambda: self._codex_auth()

        record = h.codex_source()
        windows = self.windows_by_label(record)
        # The Spark window is 80% used, tighter than either standard window,
        # and must carry its own label rather than colliding with "7d".
        self.assertIn("Spark 7d", windows)
        self.assertAlmostEqual(windows["Spark 7d"]["remaining"], 20.0)
        self.assertAlmostEqual(windows["7d"]["remaining"], 88.0)

    def test_codex_rate_limit_is_not_reported_as_zero(self):
        h = self.helper
        h.http_json = lambda *a, **k: (None, {}, 429, None)
        h.codex_auth_path = lambda: self._codex_auth()

        record = h.codex_source()
        self.assertEqual(record["state"], "rateLimited")
        self.assertNotIn("windows", record)

    def _codex_auth(self):
        path = Path(self.enterContext_tmp()) / "auth.json"
        path.write_text(json.dumps({
            "tokens": {"access_token": "not-a-real-token", "account_id": "acct"}
        }), encoding="utf-8")
        return path

    def enterContext_tmp(self):
        import tempfile
        temp = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(temp, ignore_errors=True))
        return temp

    # --- Claude ----------------------------------------------------------

    def test_claude_payload_becomes_percent_windows(self):
        h = self.helper
        h.claude_access_token = lambda stale_token=None: ("not-a-real-token", "")
        h.claude_credentials_path = lambda: Path(self.enterContext_tmp()) / "missing.json"
        h.claude_usage_request = lambda token: (fixture("claude-usage.json"), 200, None)

        record = h.claude_source()
        self.assertEqual(record["state"], "ok")
        windows = self.windows_by_label(record)
        self.assertAlmostEqual(windows["5h"]["remaining"], 75.0)
        self.assertAlmostEqual(windows["7d"]["remaining"], 92.0)

    def test_claude_per_model_weekly_window_is_kept(self):
        h = self.helper
        h.claude_access_token = lambda stale_token=None: ("not-a-real-token", "")
        h.claude_credentials_path = lambda: Path(self.enterContext_tmp()) / "missing.json"
        h.claude_usage_request = lambda token: (fixture("claude-usage.json"), 200, None)

        windows = self.windows_by_label(h.claude_source())
        self.assertIn("Opus 7d", windows)
        self.assertAlmostEqual(windows["Opus 7d"]["remaining"], 37.0)

    def test_claude_expired_login_is_not_a_number(self):
        h = self.helper
        h.claude_access_token = lambda stale_token=None: ("not-a-real-token", "")
        h.claude_credentials_path = lambda: Path(self.enterContext_tmp()) / "missing.json"
        h.claude_usage_request = lambda token: (None, 401, None)

        record = h.claude_source()
        self.assertEqual(record["state"], "unauthenticated")
        self.assertNotIn("windows", record)

    # --- Copilot ---------------------------------------------------------

    def test_copilot_payload_becomes_a_counted_window(self):
        h = self.helper
        h.shutil_which = lambda name: "/usr/bin/gh"
        h.subprocess.run = lambda *a, **k: subprocess.CompletedProcess(
            a[0] if a else [], 0, json.dumps(fixture("copilot-user.json")), "")

        record = h.copilot_source()
        self.assertEqual(record["state"], "ok")
        window = record["windows"][0]
        self.assertEqual(window["remaining"], 217)
        self.assertEqual(window["limit"], 300)
        self.assertEqual(window["unit"], "count")

    def test_copilot_unlimited_is_not_converted_to_a_total(self):
        h = self.helper
        payload = fixture("copilot-user.json")
        payload["quota_snapshots"]["premium_interactions"] = {"unlimited": True}
        h.shutil_which = lambda name: "/usr/bin/gh"
        h.subprocess.run = lambda *a, **k: subprocess.CompletedProcess(
            a[0] if a else [], 0, json.dumps(payload), "")

        record = h.copilot_source()
        self.assertEqual(record["state"], "ok")
        self.assertNotIn("windows", record)
        self.assertIn("unlimited", record["detail"])


class NoNetworkTest(unittest.TestCase):
    """The guard is only worth having if it actually refuses a connection."""

    def test_outbound_connections_are_blocked(self):
        import socket
        if not hasattr(socket, "create_connection"):
            self.skipTest("no socket module")
        try:
            import sitecustomize
        except ImportError:
            self.skipTest("guard not on PYTHONPATH; run via tests/run-offline.sh")
        with self.assertRaises(OSError):
            socket.create_connection(("example.com", 443), timeout=2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
