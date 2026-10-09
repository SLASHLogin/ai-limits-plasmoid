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
import tempfile
import unittest
from datetime import datetime, timezone
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

    def test_codex_flat_login_from_cliproxyapi_is_read(self):
        """CLIProxyAPI keeps the same token fields at the top level, not under "tokens"."""
        h = self.helper
        seen = {}

        def fake_request(url, headers, *a, **k):
            seen["auth"] = headers["Authorization"]
            seen["account"] = headers.get("ChatGPT-Account-Id")
            return fixture("codex-usage.json"), {}, 200, None

        h.http_json = fake_request
        h.codex_auth_path = lambda: self._codex_auth(flat=True)

        record = h.codex_source()
        self.assertEqual(record["state"], "ok")
        self.assertEqual(seen["auth"], "Bearer not-a-real-token")
        self.assertEqual(seen["account"], "acct")

    def test_refresh_keeps_hardlinked_login_in_sync(self):
        """A refreshed token must reach CLIProxyAPI's copy, not just a replaced file."""
        h = self.helper
        temp = Path(self.enterContext_tmp())
        cliproxy = temp / "cliproxy.json"
        cliproxy.write_text(json.dumps({
            "access_token": "old-token", "refresh_token": "refresh", "account_id": "acct"
        }), encoding="utf-8")
        link = temp / "auth.json"
        os.link(cliproxy, link)
        responses = [
            (None, {}, 401, None),
            ({"access_token": "new-token"}, {}, 200, None),
            (fixture("codex-usage.json"), {}, 200, None),
        ]
        h.http_json = lambda *a, **k: responses.pop(0)
        h.codex_auth_path = lambda: link

        self.assertEqual(h.codex_source()["state"], "ok")
        self.assertEqual(json.loads(cliproxy.read_text(encoding="utf-8"))["access_token"], "new-token")
        self.assertEqual(os.stat(link).st_ino, os.stat(cliproxy).st_ino)

    def _codex_auth(self, flat=False):
        path = Path(self.enterContext_tmp()) / "auth.json"
        tokens = {"access_token": "not-a-real-token", "account_id": "acct"}
        path.write_text(json.dumps(tokens if flat else {"tokens": tokens}), encoding="utf-8")
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

    # --- Mistral ---------------------------------------------------------

    def stub_mistral_http(self, subscription=None, usage=None, sub_status=200, usage_status=200):
        """Answer both billing endpoints and record what was asked of them."""
        h = self.helper
        h.mistral_api_key = lambda: "not-a-real-mistral-key"
        seen = {}

        def fake_request(url, headers, *a, **k):
            seen["authorization"] = headers.get("Authorization")
            if url.startswith(h.MISTRAL_SUBSCRIPTION_URL):
                return subscription, {}, sub_status, None
            if url.startswith(h.MISTRAL_USAGE_URL):
                seen["usage_url"] = url
                return usage, {}, usage_status, None
            raise AssertionError("unexpected request to " + url)

        h.http_json = fake_request
        return seen

    def test_mistral_payload_becomes_a_monthly_window(self):
        h = self.helper
        seen = self.stub_mistral_http(fixture("mistral-subscription.json"),
                                      fixture("mistral-usage.json"))

        record = h.mistral_source()
        self.assertEqual(record["state"], "ok")
        window = record["windows"][0]
        self.assertEqual(window["id"], "monthly")
        self.assertEqual(window["label"], "Month")
        self.assertEqual(window["unit"], "count")
        # 9.75 of the 27 EUR allowance spent leaves 17.25.
        self.assertAlmostEqual(window["limit"], 27.0)
        self.assertAlmostEqual(window["used"], 9.75)
        self.assertAlmostEqual(window["remaining"], 17.25)
        self.assertEqual(seen["authorization"], "Bearer not-a-real-mistral-key")
        self.assertEqual(record["detail"], "Mistral Pro · €12.5 credits")

        # The spend is read for the current calendar month.
        query = dict(part.split("=", 1) for part in seen["usage_url"].split("?", 1)[1].split("&"))
        now = datetime.now(timezone.utc)
        self.assertEqual(query["start_date"], now.strftime("%Y-%m-01"))
        self.assertEqual(query["end_date"], now.strftime("%Y-%m-%d"))

        # The allowance resets at midnight UTC on the first of next month.
        reset = datetime.fromisoformat(window["resetAt"])
        self.assertEqual((reset.day, reset.hour, reset.minute, reset.second), (1, 0, 0, 0))
        self.assertEqual(reset.utcoffset(), timezone.utc.utcoffset(None))
        if now.month == 12:
            self.assertEqual((reset.year, reset.month), (now.year + 1, 1))
        else:
            self.assertEqual((reset.year, reset.month), (now.year, now.month + 1))

    def test_mistral_spend_falls_back_to_daily_rows(self):
        """A payload without a top-level total still sums its rows."""
        h = self.helper
        usage = fixture("mistral-usage.json")
        del usage["total_cost"]
        self.stub_mistral_http(fixture("mistral-subscription.json"), usage)

        record = h.mistral_source()
        self.assertEqual(record["state"], "ok")
        self.assertAlmostEqual(record["windows"][0]["used"], 9.75)

    def test_mistral_missing_spend_is_unknown_not_zero(self):
        h = self.helper
        self.stub_mistral_http(fixture("mistral-subscription.json"), {"object": "list"})

        record = h.mistral_source()
        self.assertEqual(record["state"], "unknown")
        self.assertNotIn("windows", record)

    def test_mistral_spend_past_the_allowance_is_zero_not_negative(self):
        """Pay-as-you-go usage beyond the allowance floors remaining at zero."""
        h = self.helper
        self.stub_mistral_http(fixture("mistral-subscription.json"),
                               {"object": "list", "data": [], "total_cost": 40.0})

        record = h.mistral_source()
        self.assertEqual(record["state"], "ok")
        window = record["windows"][0]
        self.assertEqual(window["remaining"], 0)
        self.assertAlmostEqual(window["used"], 40.0)

    def test_mistral_account_without_a_budget_shows_no_window(self):
        """A pay-as-you-go key has a credit balance, not a monthly allowance."""
        h = self.helper
        seen = self.stub_mistral_http({"plan": "scale", "monthly_budget": None, "credit_balance": 30.0})

        record = h.mistral_source()
        self.assertEqual(record["state"], "ok")
        self.assertNotIn("windows", record)
        self.assertEqual(record["detail"], "Mistral Scale · €30 credits")
        # No allowance means no spend request either.
        self.assertNotIn("usage_url", seen)

    def test_mistral_missing_key_is_unauthenticated(self):
        h = self.helper
        h.mistral_api_key = lambda: None
        h.http_json = lambda *a, **k: (_ for _ in ()).throw(AssertionError("no request without a key"))

        record = h.mistral_source()
        self.assertEqual(record["state"], "unauthenticated")
        self.assertNotIn("windows", record)

    def test_mistral_rejected_key_is_not_a_number(self):
        h = self.helper
        self.stub_mistral_http(sub_status=401)

        record = h.mistral_source()
        self.assertEqual(record["state"], "unauthenticated")
        self.assertNotIn("windows", record)

    def test_mistral_rate_limit_is_not_reported_as_zero(self):
        h = self.helper
        self.stub_mistral_http(sub_status=429)

        record = h.mistral_source()
        self.assertEqual(record["state"], "rateLimited")
        self.assertNotIn("windows", record)

    def test_mistral_usage_failure_is_an_explicit_error(self):
        h = self.helper
        self.stub_mistral_http(fixture("mistral-subscription.json"), usage_status=500)

        record = h.mistral_source()
        self.assertEqual(record["state"], "error")
        self.assertNotIn("windows", record)


class MistralKeyTest(unittest.TestCase):
    """The key is read the way the Vibe CLI reads it: env first, then ~/.vibe/.env."""

    def setUp(self):
        self.helper = load_helper()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.saved_environ = os.environ.copy()

        def restore():
            os.environ.clear()
            os.environ.update(self.saved_environ)

        self.addCleanup(restore)
        os.environ["HOME"] = str(self.home)
        os.environ.pop("MISTRAL_API_KEY", None)
        os.environ.pop("VIBE_HOME", None)

    def write_env_file(self, text, vibe_home=False):
        base = Path(os.environ["VIBE_HOME"]) if vibe_home else self.home / ".vibe"
        base.mkdir(parents=True, exist_ok=True)
        (base / ".env").write_text(text, encoding="utf-8")

    def test_environment_variable_is_read_first(self):
        self.write_env_file("MISTRAL_API_KEY=from-file\n")
        os.environ["MISTRAL_API_KEY"] = " from-env "
        self.assertEqual(self.helper.mistral_api_key(), "from-env")

    def test_vibe_env_file_supplies_the_key(self):
        self.write_env_file("# vibe credentials\nMISTRAL_API_KEY='mstrl_from_file'\nOTHER_KEY=x\n")
        self.assertEqual(self.helper.mistral_api_key(), "mstrl_from_file")

    def test_vibe_home_overrides_the_default_directory(self):
        os.environ["VIBE_HOME"] = str(self.home / "elsewhere")
        self.write_env_file("MISTRAL_API_KEY=from-home\n")
        self.write_env_file("MISTRAL_API_KEY=from-vibe-home\n", vibe_home=True)
        self.assertEqual(self.helper.mistral_api_key(), "from-vibe-home")

    def test_env_file_ignores_comments_and_double_quotes(self):
        self.write_env_file('# comment\n\nMISTRAL_API_KEY = "mstrl_quoted" \nexport OTHER=1\n')
        self.assertEqual(self.helper.mistral_api_key(), "mstrl_quoted")

    def test_no_key_anywhere_is_none(self):
        self.assertIsNone(self.helper.mistral_api_key())


class CodexBarInteropTest(unittest.TestCase):
    """CodexBar is optional: absent it changes nothing, present it adds rows."""

    def setUp(self):
        self.helper = load_helper()

    def stub_cli(self, payload, returncode=0):
        h = self.helper
        h.shutil_which = lambda name: "/usr/bin/codexbar" if name == "codexbar" else None
        h.subprocess.run = lambda *a, **k: subprocess.CompletedProcess(
            a[0] if a else [], returncode, json.dumps(payload), "")

    def test_absent_cli_adds_nothing(self):
        h = self.helper
        h.shutil_which = lambda name: None
        self.assertEqual(h.codexbar_extra_providers(set()), [])

    def test_only_providers_without_a_native_collector_are_added(self):
        """The native collectors need no binary, so they must keep their own rows."""
        self.stub_cli(fixture("codexbar-usage.json"))
        rows = self.helper.codexbar_extra_providers({"codex", "claude", "copilot", "mistral"})
        ids = [r["id"] for r in rows]
        self.assertNotIn("codexbar:codex", ids)
        self.assertIn("codexbar:cursor", ids)

    def test_window_minutes_become_this_widget_s_labels(self):
        self.stub_cli(fixture("codexbar-usage.json"))
        rows = self.helper.codexbar_extra_providers({"codex", "claude", "copilot", "mistral"})
        cursor = next(r for r in rows if r["id"] == "codexbar:cursor")
        labels = {w["label"]: w for w in cursor["windows"]}
        self.assertIn("5h", labels)
        self.assertIn("7d", labels)
        # 40% used must be reported as 60 remaining.
        self.assertAlmostEqual(labels["5h"]["remaining"], 60.0)

    def test_extra_rate_window_keeps_its_own_title(self):
        """A tighter per-feature cap must not hide behind a looser window."""
        self.stub_cli(fixture("codexbar-usage.json"))
        rows = self.helper.codexbar_extra_providers({"codex", "claude", "copilot", "mistral"})
        cursor = next(r for r in rows if r["id"] == "codexbar:cursor")
        labels = {w["label"]: w for w in cursor["windows"]}
        self.assertIn("Fast requests", labels)
        self.assertAlmostEqual(labels["Fast requests"]["remaining"], 15.0)

    def test_provider_with_no_windows_is_skipped(self):
        self.stub_cli(fixture("codexbar-usage.json"))
        rows = self.helper.codexbar_extra_providers({"codex", "claude", "copilot", "mistral"})
        self.assertNotIn("codexbar:gemini", [r["id"] for r in rows])

    def test_failing_cli_is_not_an_error_row(self):
        """An unusable CodexBar must degrade to silence, not a broken row."""
        self.stub_cli({}, returncode=1)
        self.assertEqual(self.helper.codexbar_extra_providers(set()), [])


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
