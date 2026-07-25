#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HELPER = Path(os.environ.get("LIMIT_WIDGET_HELPER", ROOT / "helper/limit-widget-helper"))
CLAUDE_BRIDGE = ROOT / "helper/limit-widget-claude-statusline"


class HelperTest(unittest.TestCase):
    def run_helper(self, config_files=None):
        with tempfile.TemporaryDirectory() as temp:
            config_home = Path(temp) / "config"
            config_dir = config_home / "limit-widget"
            config_dir.mkdir(parents=True)
            for name, payload in (config_files or {}).items():
                (config_dir / name).write_text(json.dumps(payload), encoding="utf-8")

            env = os.environ.copy()
            env["XDG_CONFIG_HOME"] = str(config_home)
            env["LIMIT_WIDGET_DISABLE_AUTO"] = "1"
            completed = subprocess.run(
                [str(HELPER), "--json"],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            return json.loads(completed.stdout)

    def test_empty_configuration_is_explicitly_unknown(self):
        payload = self.run_helper()
        self.assertEqual(payload["version"], 2)
        self.assertEqual([p["id"] for p in payload["providers"]], ["codex", "claude", "copilot"])
        self.assertTrue(all(p["state"] == "unsupported" for p in payload["providers"]))
        self.assertTrue(all(p["remaining"] is None for p in payload["providers"]))

    def test_snapshot_is_normalized_and_used_can_be_derived(self):
        payload = self.run_helper({
            "limits.json": {
                "providers": {
                    "codex": {"used": 25, "limit": 100, "detail": "test window"},
                    "claude": {"remaining": -1, "limit": 100},
                }
            }
        })
        codex, claude, _ = payload["providers"]
        self.assertEqual(codex["remaining"], 75)
        self.assertEqual(codex["state"], "ok")
        self.assertIsNone(claude["remaining"])
        self.assertEqual(claude["state"], "unknown")

    def test_command_source_is_opt_in_and_precedes_snapshot(self):
        command = [
            sys.executable,
            "-c",
            'print("{\\"remaining\\": 7, \\"limit\\": 20, \\"detail\\": \\"local command\\"}")',
        ]
        payload = self.run_helper({
            "limits.json": {"codex": {"remaining": 1, "limit": 2}},
            "providers.json": {"providers": {"codex": {"command": command}}},
        })
        codex = payload["providers"][0]
        self.assertEqual(codex["remaining"], 7)
        self.assertEqual(codex["limit"], 20)
        self.assertEqual(codex["detail"], "local command")

    def test_multiple_windows_are_preserved(self):
        payload = self.run_helper({
            "limits.json": {
                "providers": {
                    "claude": {
                        "windows": [
                            {"id": "five_hour", "label": "5h", "remaining": 72, "limit": 100},
                            {"id": "seven_day", "label": "7d", "remaining": 91, "limit": 100},
                        ]
                    }
                }
            }
        })
        claude = payload["providers"][1]
        self.assertEqual([w["label"] for w in claude["windows"]], ["5h", "7d"])
        self.assertEqual(claude["remaining"], 72)

    def test_failed_command_does_not_fall_back_to_old_number(self):
        payload = self.run_helper({
            "limits.json": {"codex": {"remaining": 1, "limit": 2}},
            "providers.json": {"providers": {"codex": {"command": ["definitely-not-a-real-command"]}}},
        })
        codex = payload["providers"][0]
        self.assertEqual(codex["state"], "error")
        self.assertIsNone(codex["remaining"])

    def test_elapsed_claude_window_becomes_zero_used(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            config_home = home / "config"
            config_dir = config_home / "limit-widget"
            config_dir.mkdir(parents=True)
            cache = {
                "providers": {
                    "claude": {
                        "state": "ok",
                        "windows": [
                            {
                                "id": "five_hour",
                                "label": "5h",
                                "remaining": 1,
                                "limit": 100,
                                "used": 99,
                                "usedPercentage": 99,
                                "resetAt": "2020-01-01T00:00:00+00:00",
                            },
                            {
                                "id": "seven_day",
                                "label": "7d",
                                "remaining": 30,
                                "limit": 100,
                                "used": 70,
                                "usedPercentage": 70,
                                "resetAt": "2100-01-01T00:00:00+00:00",
                            },
                        ],
                    }
                }
            }
            (config_dir / "claude-limits.json").write_text(json.dumps(cache), encoding="utf-8")
            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(config_home),
                "CODEX_HOME": str(home / "codex"),
                "PATH": "",
            })
            completed = subprocess.run(
                [sys.executable, str(HELPER), "--json"],
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            payload = json.loads(completed.stdout)
            windows = payload["providers"][1]["windows"]
            self.assertEqual([window["usedPercentage"] for window in windows], [0.0, 70.0])
            self.assertEqual([window["remaining"] for window in windows], [100, 30])


class ClaudeBridgeTest(unittest.TestCase):
    def test_used_percentage_is_inverted_to_remaining(self):
        with tempfile.TemporaryDirectory() as temp:
            config_home = Path(temp) / "config"
            env = os.environ.copy()
            env["XDG_CONFIG_HOME"] = str(config_home)
            payload = {
                "rate_limits": {
                    "five_hour": {"used_percentage": 20, "resets_at": 1782600000},
                    "seven_day": {"used_percentage": 65, "resets_at": 1783000000},
                }
            }
            subprocess.run(
                [str(CLAUDE_BRIDGE)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=True,
                env=env,
            )
            cached = json.loads((config_home / "limit-widget" / "claude-limits.json").read_text())
            windows = cached["providers"]["claude"]["windows"]
            self.assertEqual([window["usedPercentage"] for window in windows], [20, 65])
            self.assertEqual([window["remaining"] for window in windows], [80, 35])


if __name__ == "__main__":
    unittest.main()
