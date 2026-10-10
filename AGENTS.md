# AGENTS.md — AI Limits (KDE Plasma 6 widget)

This file captures conventions and preferences learned from the project's
development history. Follow these unless the user explicitly asks otherwise.

## Project overview

A Plasma 6 panel widget that shows AI service usage limits (ChatGPT, Claude
Code, GitHub Copilot, Mistral Vibe) in a compact panel representation with a
detailed popup. The collector is a Python script shipped inside the widget
package; the UI is QML.

```
package/contents/
├── tools/limit-widget-helper     # Python collector (single file)
├── ui/main.qml                   # PlasmoidItem — panel + popup
├── ui/ProviderRow.qml            # One provider row (popup)
├── ui/config/ConfigGeneral.qml   # Settings page (KCM.SimpleKCM)
├── config/config.qml             # Config category definition
├── config/main.xml               # Config schema (settings keys)
└── icons/                        # Symbolic SVGs per provider
tests/
├── run-offline.sh                # Test runner (network blocked)
├── test_helper.py                # Collector unit tests
├── test_vendor_parsing.py        # Vendor response fixture tests
└── fixtures/                     # Recorded vendor JSON responses
```

## Build, test, install

```sh
./tests/run-offline.sh                                  # full test suite, network blocked
kpackagetool6 --type Plasma/Applet --upgrade package    # install/update the widget
plasmawindowed dev.slashlogin.ailimits                  # run standalone for testing
```

After changing QML files, the installed widget needs a reload to pick them up.
plasmashell caches compiled QML aggressively — use `plasmashell --replace`
(not a systemd restart) to bust the cache:

```sh
cp package/contents/ui/*.qml ~/.local/share/plasma/plasmoids/dev.slashlogin.ailimits/contents/ui/
rm -rf ~/.cache/plasmashell/qmlcache
nohup plasmashell --replace > /tmp/plasmashell-replace.log 2>&1 &
```

## Commit conventions

- **Minimal commits.** One logical change per commit. The user has explicitly
  asked: "Keep committing each change as minimal change commit."
- **Do not release unless asked.** The user says "commit and push changes, do
  not release new version yet" when they want commits pushed without a tag.
  Only tag and push a release when the user says "release", "make a new
  release", or "let's release".
- **DCO sign-off**: use `git commit -s`.
- **CHANGELOG**: feature/fix commits add a CHANGELOG entry under a new version
  heading (bump `package/metadata.json` version too). The release commit is
  just the tag.
- **SPDX headers** on every source file:
  ```
  SPDX-FileCopyrightText: 2026 SLASHLogin
  SPDX-License-Identifier: GPL-3.0-or-later
  ```

## UI/UX preferences

These are hard-won preferences from iterative visual review. Respect them.

### Naming

- Use **short names**. "Codex / ChatGPT" → "ChatGPT". "API Usage" → "API".
  "Vibe Code Usage" → "Vibe Code".
- Provider short names in the panel are single letters: C, A, G, M.

### Panel (taskbar) display

- Show **both values** when a provider has multiple windows (e.g. `64%/36%`
  for Mistral's Month/Vibe, `100%/0%` for Codex's 5h/7d).
- When a rolling window is exhausted (0%), the panel shows **only the time
  until reset** as a bare duration — no percentages, no "resets" word, no
  period label. Example: `5H` or `7D` or `30min`.
- Use the **biggest denominator** for durations: `3d`, `6h`, `30min`, `15s`.
- **Capitalize** period labels: `5h` → `5H`, `7d` → `7D` (including per-model
  variants like `Opus 7D`).
- The panel width should **shrink** when providers are hidden — do not stretch
  remaining elements across the freed space.
- The panel should have **equal margins** on left and right edges.
- Providers should have **comfortable spacing** between them (not too tight).

### Popup display

- The reset hint uses **"R"** (not "resets"): `R 5H 30min`, `R 5H 14 Oct 12:25`.
- Period labels are **capitalized**: `5H`, `7D`, `Opus 7D`.
- The popup should be **wide enough** that text never elides to "...".
- The popup's reset text format is **configurable** in settings: short
  duration / long date / both.
- The popup lists **every** visible provider row — it is NOT affected by the
  "Hide providers with no usage yet" setting.
- Multi-window providers use the **same font size** as single-window ones.
- The **Refresh** button and the **globe (Usage)** button must be the same
  size (28×28), aligned horizontally, and share the same style (neither flat).
- The globe button must be **square**.
- Use the **product logo** (`product-logo.svg`) in the popup header and
  settings page — not the old `view-statistics` icon.

### Settings page

- Root must be `KCM.SimpleKCM` (gives standard margins at the top).
- The config source path in `config.qml` is resolved **relative to
  `contents/ui/`**, so use `"config/ConfigGeneral.qml"` — not
  `"ui/config/ConfigGeneral.qml"`.
- The settings page must actually render (not show empty/old view). If it
  doesn't, check the `source` path in `config.qml` first.

### "Hide providers with no usage yet" setting

- Applies to the **panel/taskbar only** — the popup always shows all rows.
- A provider at **100% (untouched allowance)** counts as "no usage yet" and
  should be hidden.
- Signed-out (`unauthenticated`) and allowance-less providers are hidden.
- **Error/rate-limited** rows stay visible (a failure is not "not started").
- Windows with no measurable numbers (unlimited plans) keep their provider
  visible.

### Provider ordering

- Providers can be **reordered** from settings (up/down buttons per row).
- The saved order applies to the panel, popup, and tooltip.
- A newly reported provider appears at the end until moved.

### Screenshots

- Update screenshots in `screenshots/` when the UI changes significantly.
- Both **light and dark** theme variants are needed.

## Helper / collector conventions

- The collector is **one Python file**: `package/contents/tools/limit-widget-helper`.
- Each provider is a self-contained function returning normalized windows.
- `limits.json` is a **fallback only** — a live sign-in always wins. A snapshot
  must never shadow live values.
- Unknown values stay `—`; never substitute zero.
- Mistral values come from `admin.mistral.ai/subscription` with a pasted
  browser session cookie (opt-in via `providers.json`). The API key path does
  not work (endpoints return 404).
- All network requests go directly to providers over HTTPS.
- Credentials never cross into QML — only normalized numbers do.

## Adding a provider

1. Add a spec to `PROVIDERS` in `package/contents/tools/limit-widget-helper`.
2. Return windows through `normalize_window`, with `unit` set to `"percent"`
   or `"count"`.
3. Add a symbolic 24px SVG to `package/contents/icons/` and record its source
   and license in `THIRD_PARTY_NOTICES.md`.
4. Cover the new source in `tests/test_helper.py` with a fixture, not a live
   request.
5. Update `docs/provider-support.md`, `README.md`, and `CHANGELOG.md`.

## Testing

- Always run `./tests/run-offline.sh` before committing. It blocks outbound
  network access so tests cannot accidentally hit real APIs.
- Vendor responses are parsed from recorded fixtures in `tests/fixtures/`.
- `qmllint` is available at `/usr/lib/qt6/bin/qmllint` for QML syntax checks.

## Release process

When the user asks to release:

1. Verify: `./tests/run-offline.sh`, `./tools/make-store-archive.sh`
2. Bump version in `package/metadata.json` (already done in feature commits)
3. Tag: `git tag -a "v<version>" -m "AI Limits <version>"` (matching the
   `v1.2.1` annotated tag format)
4. Push: `git push origin main && git push origin v<version>`
5. The release workflow (`.github/workflows/release.yml`) verifies, builds the
   archive, audits it, and publishes the GitHub release.

## Communication style

- The user gives **terse, direct instructions** — often one-liners. Execute
  them without asking for confirmation.
- The user frequently says **"Continue"** when an agent pauses — just keep
  going.
- The user **reviews visually** — they install and look at the widget after
  changes. Expect follow-up adjustments ("the margins are off", "too close",
  "make them the same size").
- When the user says **"reload my installed widget"**, sync changed files to
  the installed plasmoid and restart plasmashell with `--replace`.
- The user expects **minimal, focused changes** — do not refactor unrelated
  code.
