# Alternatives, and where this widget sits

Surveyed 2026-09-10. Star counts and dates are from the GitHub API on that day.

## KDE Plasma widgets

| Project | Stars | Licence | Providers | Extra binary needed | Last push |
| --- | --- | --- | --- | --- | --- |
| **AI Limits** (this) | — | GPL-3.0-or-later | 3 native, +CodexBar's when installed | no | active |
| [psimaker/codexbar-plasmoid](https://github.com/psimaker/codexbar-plasmoid) | 16 | **none declared** | many (CodexBar port) | — | 2026-08-19 |
| [EvilFreelancer/CodexBar-KDE](https://github.com/EvilFreelancer/CodexBar-KDE) | 3 | MIT | 58, via CodexBar | yes, ~50 MB | 2026-07-13 |
| [CraigBorrows/claude-usage-widget](https://github.com/CraigBorrows/claude-usage-widget) | 3 | MIT | Claude only | no | 2026-08-08 |
| [fuziontech/claude-quota-widget](https://github.com/fuziontech/claude-quota-widget) | 2 | MIT | Claude only | ccusage | 2026-07-07 |

Nobody has won this category. The largest is 16 stars, and three of the four
had not been touched for a month or more at the time of writing.

Note that `psimaker/codexbar-plasmoid` declares no licence, so its code cannot
be reused here regardless of how useful it looks. GitHub reports
`NOASSERTION`, which means no licence file it recognises.

## macOS, where the users actually are

| Project | Stars | Licence | Notes |
| --- | --- | --- | --- |
| [steipete/CodexBar](https://github.com/steipete/CodexBar) | 21,211 | MIT | Menu-bar app, 69 providers, also ships a **Linux CLI** |
| [Blimp-Labs/claude-usage-bar](https://github.com/Blimp-Labs/claude-usage-bar) | 477 | BSD-2-Clause | Claude only |

CodexBar is three orders of magnitude more popular than anything on the KDE
side, and it is the upstream that most of the KDE widgets above wrap.

## What this widget does differently

1. **Nothing to install.** The collector ships inside the KPackage, so a KDE
   Store install works immediately. Every other multi-provider Plasma widget
   requires the user to fetch a ~50 MB CodexBar tarball first, which is most of
   the reason they have not spread.
2. **Claude without a status line.** Usage is read from the endpoint behind
   Claude Code's own `/usage`, so numbers are current whether or not Claude
   Code is running.
3. **It refuses to guess.** An unreadable value stays `—`; it is never shown
   as zero, and an elapsed window is reported as stale rather than reset.
4. **Tested.** Vendor responses are parsed from recorded fixtures and the suite
   runs with outbound network blocked, so a change cannot be validated against
   one maintainer's live account.

## Reusing CodexBar rather than competing with its coverage

Breadth is the one place this widget is behind, and re-deriving 69 provider
integrations would be a poor use of anyone's time.

So the CodexBar CLI is supported as an optional source. If `codexbar` is on
`PATH`, the collector runs `codexbar usage --format json` and adds the
providers it reports that have no native collector here. Codex, Claude and
Copilot keep their built-in ones, so the zero-install property survives.

That gives a strictly better position than the wrappers: works out of the box
like the Claude-only widgets, reaches CodexBar's coverage like the wrappers do
when the user wants it, and degrades to the native three if the binary is
removed.

CodexBar is MIT. Nothing from it is bundled, redistributed, or linked — it is
an external program the user chooses to install, invoked over a documented
JSON interface. Attribution is in `THIRD_PARTY_NOTICES.md` and the README.
