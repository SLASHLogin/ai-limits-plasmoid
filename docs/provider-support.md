# Provider support matrix

The helper now performs best-effort automatic collection using the same local
sign-ins as the provider CLIs. It never prints or sends credentials to QML.
A provider may expose more than one window; Claude and Codex report a rolling
five-hour window plus a seven-day window where available.

| Provider | Automatic source | Values shown | Caveat |
| --- | --- | --- | --- |
| Codex / ChatGPT | `~/.codex/auth.json` / `$CODEX_HOME`, then `GET https://chatgpt.com/backend-api/wham/usage` | 5h, 7d, and Codex Spark windows when returned | This is a Codex client endpoint, not a stable public third-party API. |
| Claude Code | `rate_limits.five_hour` and `rate_limits.seven_day` from the documented status-line JSON, persisted by `limit-widget-claude-statusline` | 5h and 7d percentage remaining, plus reset times | The cache updates when Claude Code runs its status line. |
| GitHub Copilot | `gh api copilot_internal/user`, using GitHub CLI's credential store | Premium-interaction remaining / entitlement and monthly reset | `copilot_internal/user` is used by current clients but is not documented as a public REST endpoint. |

Official usage pages remain available from each popup row:

- [ChatGPT usage](https://chatgpt.com/settings/usage)
- [Claude usage](https://claude.ai/settings/usage)
- [Copilot usage limits](https://docs.github.com/en/copilot/concepts/usage-limits)

## Claude Code setup

Claude Code's status-line documentation defines
`rate_limits.*.used_percentage` as the percentage of the five-hour or seven-day
limit **consumed**, from 0 to 100, and `resets_at` as the Unix reset timestamp:
<https://code.claude.com/docs/en/statusline>. The widget converts this to
remaining percentage (`100 - used_percentage`) so it has the same direction as
Codex and Copilot. Both the panel and the popup show remaining, and the popup
labels it `left`; no view shows the native used percentage, because two
directions in one widget invite reading `99%` as nearly exhausted.

The easiest setup is:

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
