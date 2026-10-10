# Changelog

## Unreleased

- New: providers can be reordered. Each row in the settings' provider list
  carries an up and a down button, and the saved order applies to the panel,
  the popup, and the tooltip alike. A newly supported provider appears at
  the end until it is moved.
- New: "Hide providers with no usage yet" now applies to the panel alone and
  also treats an untouched allowance as no usage — a provider whose every
  window sits at its full 100% hides alongside signed-out and allowance-less
  ones. The popup keeps listing every row. A window that carries no numbers
  (an unlimited plan, whose usage cannot be measured) keeps its provider
  visible, as do transient error rows. The panel also shrinks to fit what it
  still shows instead of stretching the remaining rows across the space the
  hidden ones used to take. The widget's width now mirrors the drawn content
  exactly, so its edges are equidistant from the first and last element
  rather than leaving a wider gap on the right.
- Fixed: the settings dialog came up empty, or kept whatever page was shown
  before, instead of the widget's own settings. The General category's source
  in `config.qml` is resolved against `contents/ui`, so the
  `ui/config/ConfigGeneral.qml` path pointed at `contents/ui/ui/config/…`,
  a file that does not exist — Plasma then silently created an empty page.
  The source is now `config/ConfigGeneral.qml`, the form Plasma's own
  widgets use.

## 1.3.1

- Fixed: the Mistral row reported frozen values with false thresholds. A
  `limits.json` snapshot entry shadowed the live collector forever; a snapshot
  is now the fallback only when a provider has no live sign-in.
- Fixed: Mistral values are read from the Admin console's subscription page
  with the opt-in pasted cookie — the only place Mistral exposes a plan's
  allowances. Both allowances the page carries are shown as counted EUR
  windows: the included **API** allowance and the **Vibe Code** allowance.
  The `api.mistral.ai/v1/billing/*` endpoints the 1.3.0 collector called do
  not exist (they answer 404), so the API-key path never produced a value and
  is removed; the Vibe CLI's key is no longer consulted.
- Fixed: the popup's long multi-window value label overflowed its row and
  painted over the Usage button, and the popup was too short for the rows it
  lists, cutting the last row's Usage button off. Values now elide within
  their row, and the popup sizes itself to the rows it shows (further rows
  scroll). The horizontal scrollbar is off: the rows' width is bound to the
  popup's width, so it could never scroll.
- New: a settings toggle hides providers with no usage yet — no sign-in, or a
  plan without an allowance. Transient error rows stay visible.
- New: a settings toggle (on by default) shows the closest reset time when a
  rolling 5h/weekly window runs out, in the panel and the popup. Monthly
  allowances — Mistral's EUR windows and Copilot's premium interactions — are
  excluded, since their rows already carry their reset time.

## 1.3.0

- New: Mistral Vibe support. The collector reuses the API key the Vibe CLI
  stores (`MISTRAL_API_KEY` or `~/.vibe/.env`, `$VIBE_HOME` aware) and reads
  the subscription's monthly allowance from Mistral's billing endpoints — the
  one monthly usage pool shared across Studio, the API, and Vibe Code. The row
  shows a monthly EUR window with the plan and credit balance in its detail;
  pay-as-you-go accounts without a monthly budget show the balance only.
- The Vibe Code monthly-plan window is read too, as a second window on the
  Mistral row. It is only exposed to a browser session, so it is opt-in:
  paste the Cookie header from admin.mistral.ai into
  `{"providers": {"mistral": {"cookie": "…"}}}` in `providers.json` (keep the
  file `0600`). The helper extracts the budget from the Admin subscription
  page's embedded payload and falls back to the console's `billing.vibeUsage`
  route, forwarding only the `csrftoken` and `ory_session_*` cookies. Session
  cookies expire; the row notes it and the monthly window keeps showing.
- The panel shows both Mistral windows side by side, as it shows Codex's and
  Claude's session and weekly values.

## 1.2.1

- Fixed: a Codex login kept in CLIProxyAPI was reported as signed out. The
  collector now reads that layout too, and token refreshes keep it in sync.
- The panel shows Codex's weekly limit next to its session limit, as it does
  for Claude.

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
