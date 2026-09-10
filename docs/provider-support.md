# Provider support matrix

The helper now performs best-effort automatic collection using the same local
sign-ins as the provider CLIs. It never prints or sends credentials to QML.
A provider may expose more than one window; Claude and Codex report a rolling
five-hour window plus a seven-day window where available.

| Provider | Automatic source | Values shown | Caveat |
| --- | --- | --- | --- |
| Codex / ChatGPT | `~/.codex/auth.json` / `$CODEX_HOME`, then `GET https://chatgpt.com/backend-api/wham/usage` | 5h, 7d, and Codex Spark windows when returned | This is a Codex client endpoint, not a stable public third-party API. |
| Claude Code | `~/.claude/.credentials.json` (or `$CLAUDE_CONFIG_DIR`), then `GET https://api.anthropic.com/api/oauth/usage` | 5h and 7d percentage remaining, plus per-model weekly windows and reset times | This is the endpoint behind Claude Code's own `/usage`, not a documented public API. Falls back to the status-line cache, labelled stale. |
| GitHub Copilot | `gh api copilot_internal/user`, using GitHub CLI's credential store | Premium-interaction remaining / entitlement and monthly reset | `copilot_internal/user` is used by current clients but is not documented as a public REST endpoint. |

Official usage pages remain available from each popup row:

- [ChatGPT usage](https://chatgpt.com/settings/usage)
- [Claude usage](https://claude.ai/settings/usage)
- [Copilot usage limits](https://docs.github.com/en/copilot/concepts/usage-limits)

## Claude Code

The helper reads the same endpoint Claude Code's own `/usage` command reads,
reusing the OAuth login already stored by the CLI. Nothing has to be running:
the values are current every time the widget refreshes.

Each window is returned as `utilization`, the percentage of the limit
**consumed** from 0 to 100, plus an ISO `resets_at`. The widget converts this
to remaining percentage (`100 - utilization`) so it has the same direction as
Codex and Copilot. Both the panel and the popup show remaining, and the popup
labels it `left`; no view shows the native used percentage, because two
directions in one widget invite reading `99%` as nearly exhausted.

Alongside `five_hour` and `seven_day`, plans with per-model caps also return
`seven_day_opus` and `seven_day_sonnet`. All of them appear in the popup. The
panel shows the session window and the *tightest* weekly one, so a per-model
cap can never hide behind the combined weekly total.

If the stored access token has expired the helper refreshes it against
`https://platform.claude.com/v1/oauth/token`. Anthropic rotates the refresh
token on every exchange, so the read-modify-write is serialized with a lock
file next to the credentials and the rotated pair is written back atomically
with mode `0600`. Losing a rotation would sign the user out of Claude Code, so
the refresh re-reads the file under the lock and yields to a token Claude Code
refreshed first.

### Status-line fallback

`limit-widget-setup claude` remains supported and is only needed when the
helper cannot read a login — for example when the CLI keeps credentials
somewhere other than `~/.claude/.credentials.json`:

```sh
limit-widget-setup claude
```

This makes a mode-`0600` backup before wrapping the current command. To wrap
an existing status-line command manually in `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "limit-widget-claude-statusline --delegate bash /home/me/.claude/statusline-command.sh"
  }
}
```

The bridge writes `~/.config/limit-widget/claude-limits.json` atomically with
permissions `0600` and passes the original JSON unchanged to the delegate.
Values recovered from this cache are reported as `stale` and labelled with
their age. They are never rewritten to zero when a window's reset time passes:
an elapsed reset is not evidence that nothing was consumed since.

## Normalized source contract

A custom source in `providers.json` may print one JSON object:

```json
{
  "windows": [
    {
      "id": "five_hour",
      "label": "5h",
      "remaining": 72,
      "limit": 100,
      "resetAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "seven_day",
      "label": "7d",
      "remaining": 91,
      "limit": 100
    }
  ],
  "detail": "Subscription windows"
}
```

For a single window, `remaining` and `limit` at the top level are also
accepted. If valid `used` and `limit` are supplied instead, the helper computes
`limit - used`. Any malformed, missing, negative, or non-positive quota remains
unknown and is rendered as `—`.

Each window also carries a `unit`: `percent` renders as `72%`, `count` as
`72 / 300`. A window given as `usedPercentage`, or one whose `limit` is 100, is
treated as a percentage; anything else counts. Set `"unit": "count"` explicitly
for a counted quota that happens to have a limit of exactly 100.
