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
        # The Mistral row also reads a session cookie from the user's widget
        # configuration; tests must not depend on whatever providers.json
        # happens to sit on the machine running them.
        self.helper.mistral_cookie = lambda: None

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

    def stub_mistral_web(self, cookie=None, page=None, page_status=200,
                         fallback=None, fallback_status=200):
        """Stub the browser-session Admin page and the console fallback route."""
        h = self.helper
        h.mistral_cookie = lambda: cookie
        seen = {"calls": []}

        def fake_json(url, headers, *a, **k):
            seen["calls"].append(("json", url, headers))
            if url.startswith(h.MISTRAL_VIBE_USAGE_URL):
                return fallback, {}, fallback_status, None
            raise AssertionError("unexpected request to " + url)

        def fake_text(url, headers, *a, **k):
            seen["calls"].append(("text", url, headers))
            if page_status == 200:
                return page, 200, None
            return None, page_status, None

        h.http_json = fake_json
        h.http_text = fake_text
        return seen

    def subscription_page(self, payload):
        """Wrap one budget payload in the page's React Flight envelope."""
        body = json.dumps(payload, separators=(",", ":"))
        chunk = format(len(body.encode()), "x") + ":" + body + "\n"
        return '<script>self.__next_f.push([1,' + json.dumps(chunk) + '])</script>'

    def test_mistral_without_a_cookie_is_unauthenticated(self):
        h = self.helper
        h.mistral_cookie = lambda: None
        h.http_text = lambda *a, **k: (_ for _ in ()).throw(AssertionError("no request without a cookie"))

        record = h.mistral_source()
        self.assertEqual(record["state"], "unauthenticated")
        self.assertNotIn("windows", record)
        self.assertIn("providers.json", record["detail"])

    def test_mistral_page_yields_both_allowance_windows(self):
        h = self.helper
        page = (FIXTURES / "mistral-subscription-page.html").read_text(encoding="utf-8")
        cookie = "ory_session_default=abc123; csrftoken=tok; theme=dark"
        seen = self.stub_mistral_web(cookie=cookie, page=page)

        record = h.mistral_source()
        self.assertEqual(record["state"], "ok")
        self.assertEqual([w["id"] for w in record["windows"]], ["api", "vibe"])
        api, vibe = record["windows"]
        # The fixture page carries a 36% API budget and a 64% Vibe budget,
        # both over a 27 EUR allowance.
        self.assertEqual(api["label"], "API")
        self.assertEqual(api["unit"], "count")
        self.assertAlmostEqual(api["limit"], 27.0)
        self.assertAlmostEqual(api["used"], 9.72)
        self.assertAlmostEqual(api["remaining"], 17.28)
        self.assertEqual(api["resetAt"], "2026-11-01T00:00:00+00:00")
        self.assertEqual(vibe["label"], "Vibe Code")
        self.assertEqual(vibe["unit"], "count")
        self.assertAlmostEqual(vibe["limit"], 27.0)
        self.assertAlmostEqual(vibe["used"], 17.28)
        self.assertAlmostEqual(vibe["remaining"], 9.72)
        self.assertEqual(vibe["resetAt"], "2026-11-01T00:00:00+00:00")
        # The page carried both budgets, so the console fallback is not needed.
        self.assertFalse(any(url.startswith(h.MISTRAL_VIBE_USAGE_URL)
                             for _, url, _ in seen["calls"]))
        # The configured cookie is sent to the Admin page verbatim.
        page_call = next(c for c in seen["calls"] if c[0] == "text")
        self.assertEqual(page_call[2]["Cookie"], cookie)
        self.assertEqual(page_call[2]["Referer"], h.MISTRAL_SUBSCRIPTION_PAGE_URL)

    def test_mistral_page_without_a_vibe_budget_falls_back_to_the_console(self):
        h = self.helper
        # A page whose budget record carries only the API allowance.
        page = self.subscription_page({"budget": {"api_budget": {
            "usage_percentage": 36.0, "initial_budget": 27.0,
            "currency": "EUR", "reset_at": "2026-11-01T00:00:00.000Z",
        }}})
        cookie = "theme=dark; ory_session_default=abc123; csrftoken=tok; other=1"
        seen = self.stub_mistral_web(cookie=cookie, page=page,
                                     fallback=fixture("mistral-vibe-usage.json"))

        record = h.mistral_source()
        self.assertEqual(record["state"], "ok")
        self.assertEqual([w["id"] for w in record["windows"]], ["api", "vibe"])
        api, vibe = record["windows"]
        self.assertEqual(api["unit"], "count")
        self.assertAlmostEqual(api["remaining"], 17.28)
        # The console route answers a percentage only.
        self.assertEqual(vibe["unit"], "percent")
        self.assertEqual(vibe["usedPercentage"], 64.0)
        self.assertEqual(vibe["resetAt"], "2026-11-01T00:00:00+00:00")
        # Only the csrftoken and ory_session_* cookies cross to the console.
        fallback_call = next(c for c in seen["calls"]
                             if c[1].startswith(h.MISTRAL_VIBE_USAGE_URL))
        headers = fallback_call[2]
        self.assertEqual(headers["X-CSRFToken"], "tok")
        self.assertEqual(headers["Cookie"], "csrftoken=tok; ory_session_default=abc123")

    def test_mistral_page_without_an_api_budget_shows_only_the_vibe_window(self):
        h = self.helper
        page = self.subscription_page({"budget": {"vibe_budget": {
            "usage_percentage": 64.0, "initial_budget": 27.0,
            "currency": "EUR", "reset_at": "2026-11-01T00:00:00.000Z",
        }}})
        seen = self.stub_mistral_web(cookie="ory_session_default=abc123", page=page)

        record = h.mistral_source()
        self.assertEqual(record["state"], "ok")
        self.assertEqual([w["id"] for w in record["windows"]], ["vibe"])
        self.assertFalse(any(url.startswith(h.MISTRAL_VIBE_USAGE_URL)
                             for _, url, _ in seen["calls"]))

    def test_mistral_plan_without_any_allowance_is_a_legitimate_absence(self):
        h = self.helper
        page = self.subscription_page({"budget": {"api_budget": {
            "usage_percentage": 0.0, "initial_budget": 0.0, "currency": "EUR",
        }}})
        self.stub_mistral_web(cookie="ory_session_default=abc123; csrftoken=tok", page=page)

        record = h.mistral_source()
        self.assertEqual(record["state"], "unknown")
        self.assertNotIn("windows", record)

    def test_mistral_without_a_session_cookie_is_a_note(self):
        h = self.helper
        seen = self.stub_mistral_web(cookie="csrftoken=tok")

        record = h.mistral_source()
        self.assertEqual(record["state"], "error")
        self.assertNotIn("windows", record)
        self.assertIn("ory_session", record["detail"])
        # No request is made without a session cookie.
        self.assertEqual(seen["calls"], [])

    def test_mistral_session_expired_is_reported(self):
        h = self.helper
        self.stub_mistral_web(cookie="ory_session_default=abc123", page_status=401)

        record = h.mistral_source()
        self.assertEqual(record["state"], "unauthenticated")
        self.assertIn("expired", record["detail"])

    def test_subscription_page_fixture_yields_both_budgets(self):
        h = self.helper
        page = (FIXTURES / "mistral-subscription-page.html").read_text(encoding="utf-8")
        budgets = h.parse_subscription_budgets(page)
        self.assertIsNotNone(budgets)
        self.assertAlmostEqual(budgets["api"]["usedPercentage"], 36.0)
        self.assertAlmostEqual(budgets["vibe"]["usedPercentage"], 64.0)
        self.assertAlmostEqual(budgets["vibe"]["used"], 17.28)
        self.assertAlmostEqual(budgets["vibe"]["remaining"], 9.72)

    def test_subscription_page_without_budgets_parses_to_none(self):
        h = self.helper
        page = '<script>self.__next_f.push([1,"1:{\\"a\\":1}\\n"])</script>'
        self.assertIsNone(h.parse_subscription_budgets(page))

    def test_subscription_page_with_two_distinct_budgets_is_ambiguous(self):
        """A contradictory page reads as no data, not a wrong number."""
        h = self.helper
        first = self.subscription_page({"budget": {"vibe_budget": {
            "usage_percentage": 10.0, "initial_budget": 5.0, "currency": "EUR"}}})
        second = self.subscription_page({"budget": {"vibe_budget": {
            "usage_percentage": 20.0, "initial_budget": 5.0, "currency": "EUR"}}})
        self.assertIsNone(h.parse_subscription_budgets(first + second))

    def test_subscription_page_skips_byte_counted_text_rows(self):
        """A budget embedded in a text row's payload must not be parsed."""
        h = self.helper
        fake = json.dumps({"budget": {"vibe_budget": {
            "usage_percentage": 99.0, "initial_budget": 5.0, "currency": "EUR",
        }}}, separators=(",", ":"))
        payload = '{"note":"line one\n' + fake + '"}'
        body = "T" + format(len(payload.encode()), "x") + "," + payload
        chunk = format(len(body.encode()), "x") + ":" + body + "\n"
        page = '<script>self.__next_f.push([1,' + json.dumps(chunk) + '])</script>'
        self.assertIsNone(h.parse_subscription_budgets(page))

    def test_mistral_vibe_usage_rejects_out_of_range_percentage(self):
        h = self.helper
        payload = [{"result": {"data": {"json": {"usage_percentage": 140.0}}}}]
        h.http_json = lambda *a, **k: (payload, {}, 200, None)
        pairs = {"csrftoken": "tok", "ory_session_x": "abc"}
        self.assertIsNone(h.mistral_vibe_usage_fallback(pairs))

    def test_mistral_vibe_usage_rejects_unsafe_csrf_token(self):
        h = self.helper
        h.http_json = lambda *a, **k: (_ for _ in ()).throw(AssertionError("no request"))
        pairs = {"csrftoken": "bad;token", "ory_session_x": "abc"}
        self.assertIsNone(h.mistral_vibe_usage_fallback(pairs))


class SnapshotPrecedenceTest(unittest.TestCase):
    """A saved limits.json snapshot is the credential-free fallback.

    A live sign-in always wins over it; the snapshot is read only when no
    live credential exists, never to shadow one with frozen values.
    """

    def setUp(self):
        self.helper = load_helper()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config_home = Path(self.temp.name) / "config"
        (self.config_home / "limit-widget").mkdir(parents=True)
        self.saved_environ = os.environ.copy()

        def restore():
            os.environ.clear()
            os.environ.update(self.saved_environ)

        self.addCleanup(restore)
        os.environ["XDG_CONFIG_HOME"] = str(self.config_home)
        # Keep the optional CodexBar CLI out of the snapshot.
        os.environ["LIMIT_WIDGET_CODEXBAR"] = str(Path(self.temp.name) / "no-codexbar")

    def write_limits(self, payload):
        (self.config_home / "limit-widget" / "limits.json").write_text(
            json.dumps(payload), encoding="utf-8")

    def stub_auto(self, state):
        def auto_source(provider_id):
            if provider_id == "mistral":
                if state == "live":
                    return {"state": "ok", "windows": [{
                        "id": "api", "label": "API Usage", "unit": "count",
                        "remaining": 25.5, "limit": 25.5, "used": 0.0,
                    }]}
                return {"state": state, "detail": "stubbed"}
            return {"state": "unsupported"}
        self.helper.auto_source = auto_source

    def mistral_provider(self):
        snapshot = self.helper.snapshot()
        return next(p for p in snapshot["providers"] if p["id"] == "mistral")

    def test_live_source_wins_over_a_saved_snapshot(self):
        self.write_limits({"providers": {"mistral": {"remaining": 1, "limit": 2}}})
        self.stub_auto("live")

        provider = self.mistral_provider()
        self.assertEqual(provider["state"], "ok")
        self.assertEqual(provider["remaining"], 25.5)
        self.assertEqual(provider["limit"], 25.5)

    def test_saved_snapshot_is_used_when_no_live_sign_in_exists(self):
        self.write_limits({"providers": {"mistral": {"remaining": 17.25, "limit": 27}}})
        self.stub_auto("unauthenticated")

        provider = self.mistral_provider()
        self.assertEqual(provider["remaining"], 17.25)
        self.assertEqual(provider["limit"], 27)

    def test_live_error_does_not_fall_back_to_a_stale_snapshot(self):
        self.write_limits({"providers": {"mistral": {"remaining": 17.25, "limit": 27}}})
        self.stub_auto("error")

        provider = self.mistral_provider()
        self.assertEqual(provider["state"], "error")
        self.assertIsNone(provider["remaining"])


class MistralCookieTest(unittest.TestCase):
    """The session cookie is read from the widget's own providers.json."""

    def setUp(self):
        self.helper = load_helper()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config_home = Path(self.temp.name) / "config"
        (self.config_home / "limit-widget").mkdir(parents=True)
        self.saved = os.environ.copy()

        def restore():
            os.environ.clear()
            os.environ.update(self.saved)

        self.addCleanup(restore)
        os.environ["XDG_CONFIG_HOME"] = str(self.config_home)

    def write_providers(self, payload):
        (self.config_home / "limit-widget" / "providers.json").write_text(
            json.dumps(payload), encoding="utf-8")

    def test_cookie_is_read_from_providers_json(self):
        self.write_providers({"providers": {"mistral": {"cookie": "ory_session_x=abc; csrftoken=t"}}})
        self.assertEqual(self.helper.mistral_cookie(), "ory_session_x=abc; csrftoken=t")

    def test_cookie_header_prefix_is_stripped(self):
        self.write_providers({"providers": {"mistral": {"cookie": "Cookie: ory_session_x=abc"}}})
        self.assertEqual(self.helper.mistral_cookie(), "ory_session_x=abc")

    def test_other_providers_are_ignored(self):
        self.write_providers({"providers": {"codex": {"cookie": "nope"}}})
        self.assertIsNone(self.helper.mistral_cookie())

    def test_missing_file_is_none(self):
        self.assertIsNone(self.helper.mistral_cookie())

    def test_cookie_with_a_newline_is_rejected(self):
        self.write_providers({"providers": {"mistral": {"cookie": "ory_session_x=abc\r\nX: y"}}})
        self.assertIsNone(self.helper.mistral_cookie())


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
