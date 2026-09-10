# Changelog

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
