# KDE Store listing: what to set

Everything here is done by hand at <https://store.kde.org/> (or opendesktop.org,
the same backend). There is no upload API — see `kde-store.md`.

## Access

If the site returns a bare `Forbidden` in every browser while `curl` still
works, an Apache-level IP block is in front of it, not Anubis. Anubis evaluates
`ALLOW`/`DENY`/`CHALLENGE` per request with no ban timer, and its DENY serves a
decoy page rather than a plain `Forbidden`.

No `Retry-After` is sent, so the duration is not published anywhere. Check
without loading the site in a browser:

```sh
curl -sS -o /dev/null -w '%{http_code}\n' \
  -A 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36' \
  https://store.kde.org/p/2371022/
```

`200` from curl only proves the host answers; try a real browser to confirm.
A phone hotspot or VPN gives a different IP and sidesteps it entirely.

## Product Logo

Upload `screenshots/product-logo.png` (512×512). The Store serves it at 85×85,
a faithful proportional resize — it is not cropped.

## Gallery Pictures (order matters)

1. `screenshots/store-hero.png` — **first**. The browse listing tile uses the
   first gallery picture, not the product logo, squeezed into a 160px square.
   A dense screenshot is unreadable there; this one is composed for it.
2. `screenshots/widget-popup.png` — the detailed popup view.

## Tags (5 maximum)

```
ai, claude, monitor, productivity, panel
```

All five already exist as browse subcategories, so they carry filter traffic.
`plasmoid`, `plasma6`, and `kde-widget` are deliberately not used: the category
is already Plasma 6 Applets, so they would spend slots on reach you have.

## Description

```
AI subscription usage limits in a monochrome panel widget: Codex/ChatGPT,
Claude Code, and GitHub Copilot in one view.

Install: download the .plasmoid, then
  kpackagetool6 --type Plasma/Applet --install ai-limits-1.1.0.plasmoid
Add "AI Limits" via Edit Panel -> Add Widgets. Needs only Plasma 6 and
Python 3 - the collector ships inside the package, so nothing has to be on
PATH.

Collection is entirely local. It reads the sign-ins the Codex, Claude Code,
and GitHub CLIs already store and contacts only those providers directly. No
telemetry, no server of its own. Unknown values stay "-", never zero.

Claude usage is read live from the endpoint behind Claude Code's /usage, so
nothing needs to be running.

Optional: install the CodexBar CLI and the widget also shows the providers it
reports - Cursor, Gemini, Grok, OpenRouter and more.

Contributions are very welcome, especially for providers not yet supported:
github.com/SLASHLogin/ai-limits-plasmoid
```

## Fields already correct

Name, category, Original, GPLv3, homepage, source link, and per-file versions
are all set. When uploading a new release, use **Update** on the existing
product rather than Add Product, and set the *file's* version as well as the
product version — Get New Widgets compares the file's.
