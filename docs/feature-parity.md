# Feature parity

Compared against the settings each widget exposes and the UI files it ships,
read from their repositories on 2026-09-10. See `alternatives.md` for who
these projects are.

`psi` = psimaker/codexbar-plasmoid, `EF` = EvilFreelancer/CodexBar-KDE,
`CB` = CraigBorrows/claude-usage-widget.

| Feature | AI Limits | psi | EF | CB |
| --- | --- | --- | --- | --- |
| Works with nothing else installed | **yes** | no | no | yes |
| Providers without an extra binary | **3** | 0 | 0 | 1 |
| Providers with CodexBar installed | ~69 | ~69 | 58 | — |
| Refresh interval | yes | yes | yes | yes |
| Choose which providers to show | **yes** | yes | yes | — |
| CodexBar CLI path override | **yes** | yes | yes | — |
| Hide unavailable providers | yes | — | — | — |
| Per-model / per-feature caps | yes | — | yes | — |
| Stale values labelled with age | **yes** | — | — | — |
| Cost / spend | no | yes | yes | — |
| Burn rate / pace | no | — | yes | — |
| Usage history chart | no | — | yes | — |
| Provider status incidents | no | yes | — | — |
| Panel display modes | no | yes | — | — |
| Radial gauges | no | — | yes | — |
| Proxy support | no | — | yes | — |
| Automated tests | **yes** | — | — | — |

## Closed in 1.2.0

- **Choose which providers to show.** Both CodexBar wrappers had this and it
  matters more here now that CodexBar can contribute dozens of rows. Stored as
  a list of ids to *hide*, so a newly supported provider appears by default
  rather than being silently absent from an existing configuration. The
  settings page lists whatever the collector last reported, so providers that
  exist only through CodexBar can be switched off too.
- **CodexBar CLI path.** For installs that are not on `PATH`.

## Still missing, in the order worth doing

1. **Cost and spend.** Both wrappers show it. CodexBar exposes it through a
   second call, `codexbar cost`, with a `daily` series per provider. Only
   available when CodexBar is installed, so it cannot reach the three native
   providers without separate work per vendor.
2. **Burn rate / pace.** Computable from data already collected — the elapsed
   fraction of a window against the used fraction — for any window whose length
   is known. No new data source needed. The most useful of the three.
3. **Usage history.** Needs persistence the widget does not currently have, and
   a decision about where to keep it and for how long. Largest of the three.

Deliberately not planned: radial gauges and panel display modes are styling
rather than capability, and proxy support belongs in the collector's HTTP layer
only if someone asks for it.
