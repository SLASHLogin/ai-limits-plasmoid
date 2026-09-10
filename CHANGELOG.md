# Changelog

## 1.2.0

- New: choose which providers the widget shows, in its settings. The list is
  built from whatever the collector last reported, so providers that exist only
  through CodexBar can be switched off too. Stored as ids to hide, so a newly
  supported provider appears by default instead of being silently absent from
  an existing configuration.
- New: a CodexBar CLI path setting, for installs that are not on `PATH`.
- Added `docs/feature-parity.md` comparing this widget against the others in
  its category, including what is still missing.

## 1.1.0

- New: providers from the [CodexBar](https://github.com/steipete/CodexBar) CLI
  (MIT) are picked up when `codexbar` is on `PATH` — Cursor, Gemini, Grok,
  OpenRouter, DeepSeek, Zed, AWS Bedrock and more. It is entirely optional: the
  three built-in collectors still need nothing installed, and they keep their
  own rows. Disable with `{"codexbar": {"enabled": false}}` in `providers.json`.
- CodexBar providers appear in the popup only. The panel grows with every row
  it draws, so dozens of providers would push the rest of the panel off screen.
- Fixed: a provider reporting three or more windows pushed its own name out of
  the popup row, because the value label had no width limit and the name was
  free to elide to nothing.
- Added `docs/alternatives.md` surveying the other widgets in this space.

## 1.0.2

- The Codex row shows OpenAI's mark again, shipped unmodified and used
  nominatively. `codex-generic-symbolic.svg` is bundled alongside it as a
  neutral drop-in for redistributions that would rather not carry a brand
  asset; see `TRADEMARKS.md`.

## 1.0.1

- Fixed: a Codex Spark weekly cap was labelled `7d`, the same as the combined
  weekly window, so the popup showed two rows that could not be told apart. It
  is now labelled `Spark 7d`.
- Vendor responses are now covered by tests using recorded fixtures, and the
  test suite runs with outbound network access blocked.

## 1.0.0

First release.

- Codex/ChatGPT, Claude Code, and GitHub Copilot usage in one monochrome panel
  widget, with a popup showing every window per provider.
- Claude usage is read live from the endpoint behind Claude Code's `/usage`, so
  nothing needs to be running. Includes the 5h and 7d windows plus per-model
  weekly windows on plans that have them.
- The collector ships inside the widget package, so a KDE Store install needs
  nothing on `PATH`.
- Unknown values stay `—` and are never shown as zero.
- Licensed GPL-3.0-or-later. Provider marks are excluded from the grant under
  section 7(e); the Codex glyph is original to this project.
