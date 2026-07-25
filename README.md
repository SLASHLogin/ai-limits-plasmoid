# AI Limits — KDE Plasma 6 widget

A small Plasma 6 panel widget for keeping Codex/ChatGPT, Claude Code, and
GitHub Copilot limits in one monochrome view. The panel representation is a
single compact summary (`C  — · A  — · G  —`); clicking it opens a popup with
one symbolic row per provider.

The widget uses the local sign-ins already used by the provider CLIs; it does
not scrape browser dashboards or read browser cookies. Codex and Copilot are
read automatically when their local CLI credentials are available. Claude Code
exposes its subscription windows to its documented status-line command, so a
small bridge caches those values for the widget. Unknown values stay `—`; they
are never shown as zero.

![AI Limits expanded widget](screenshots/widget-popup.png)

## Install

Dependencies are the normal Plasma 6 runtime and Python 3 for the companion
helper. Build and install for the current user:

```sh
cmake -S . -B build -DCMAKE_INSTALL_PREFIX="$HOME/.local"
cmake --build build
cmake --install build
```

Make sure `~/.local/bin` is in the environment used to start Plasma. To test
without installing, install the package with the Plasma package tool and put
the helper on `PATH`:

```sh
kpackagetool6 --type Plasma/Applet --install package
PATH="$HOME/.local/bin:$PATH" plasmashell --replace
```

Add **AI Limits** to the panel using **Edit Panel → Add Widgets**, then drag it
next to the task manager. It is a Plasma panel widget rather than a task-manager
plugin, so it can also be placed on the desktop.

## Setup and automatic collection

After installation, the helper automatically tries:

- **Codex / ChatGPT:** the ChatGPT OAuth login in `~/.codex/auth.json` (or
  `$CODEX_HOME`). Sign in with the Codex CLI using your ChatGPT account.
- **GitHub Copilot:** `gh api copilot_internal/user`, reusing GitHub CLI's
  keychain-backed login. Run `gh auth login` if needed. This is the endpoint
  used by current Copilot clients, but GitHub does not document it as a public
  third-party API, so it may change.
- **Claude Code:** the documented `rate_limits.five_hour` and
  `rate_limits.seven_day` fields from Claude Code's status-line JSON. Run:

```sh
limit-widget-setup claude
```

This backs up `~/.claude/settings.json`, wraps your existing status-line
command, and leaves credentials untouched. The widget will show both **5h** and
**7d** after Claude Code produces its first status-line update. To configure it
manually, set your status-line command to
`limit-widget-claude-statusline --delegate ...`. The bridge stores only
percentages and reset times in `~/.config/limit-widget/claude-limits.json` with
mode `0600`.

If a CLI is not logged in, the popup gives a setup message instead of a fake
number. For a simple, credential-free snapshot, create
`~/.config/limit-widget/limits.json`:

```json
{
  "providers": {
    "codex": {
      "remaining": 12,
      "limit": 100,
      "resetAt": "2026-08-01T00:00:00Z",
      "detail": "Primary window"
    },
    "claude": {
      "remaining": 42,
      "limit": 100,
      "detail": "Five-hour window"
    },
    "copilot": {
      "remaining": 180,
      "limit": 300,
      "detail": "Premium requests"
    }
  }
}
```

For live values, use `~/.config/limit-widget/providers.json` to point at a
local command for each provider:

```json
{
  "providers": {
    "codex": { "command": ["/home/me/bin/codex-limit"] },
    "claude": { "command": ["/home/me/bin/claude-limit"] },
    "copilot": { "command": ["/home/me/bin/copilot-limit"] }
  }
}
```

Each command must print one JSON object to stdout, for example:

```json
{"remaining": 12, "limit": 100, "resetAt": "2026-08-01T00:00:00Z", "detail": "Primary window"}
```

Commands are executed without a shell, with an eight-second timeout, and only
their normalized result is sent to the widget. Keep credentials in the command
or a system secret store; do not put them in Plasma configuration or JSON files
that are world-readable. See `examples/` for copyable templates.

Refresh is five minutes by default and can be changed in the widget settings
from 1–60 minutes. Press **Refresh** in the popup for an immediate update.

## Provider limitations

- **Codex / ChatGPT:** the helper uses the same OAuth login and usage endpoint
  as the Codex CLI. OpenAI can change this client endpoint; if it stops
  working, sign in again or use a local adapter.
- **Claude Code:** the widget shows the documented five-hour and seven-day
  `rate_limits` windows from the status-line input. The values are cached from
  the last Claude status update while Claude is idle.
- **GitHub Copilot:** the helper reads the current premium-interaction quota
  through the logged-in GitHub CLI. Account tiers may expose unlimited chat or
  completion quotas, which are displayed as unlimited rather than converted to
  a made-up total.

The popup links to each provider's official usage page. See
[`docs/provider-support.md`](docs/provider-support.md) for the support matrix
and endpoint details.

## KDE Store status

The project is not yet published on KDE Store. The current Store blocker is
that the plasmoid depends on helper executables installed by CMake, while KDE
Store installs only the KPackage. See
[`docs/kde-store.md`](docs/kde-store.md) for the self-contained packaging plan
and remaining release checks.

## Development and tests

```sh
cmake -S . -B build -DBUILD_TESTING=ON
ctest --test-dir build --output-on-failure
```

The test suite uses sanitized temporary configuration and never contacts a
provider. Manual Plasma testing should cover both horizontal and vertical
panels, a missing helper, malformed JSON, and a command timeout.

## License

The widget code is MIT. Provider marks come from the user-supplied OpenAI
asset archive, Lobe Icons, and Primer Octicons; see
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
