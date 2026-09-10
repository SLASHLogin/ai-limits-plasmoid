# KDE Store publication

## Status

The `1.0.0` package is self-contained and ready to upload. The collector ships
at `contents/tools/limit-widget-helper` inside the package and is invoked
through `python3` from a package-relative path, so a Store installation works
with nothing of this project on `PATH`.

The applet id is `dev.slashlogin.ailimits`. It is deliberately not under
`org.kde.*`, which is reserved for KDE's own projects.

## Building the upload archive

```sh
./tools/make-store-archive.sh
```

This writes `dist/ai-limits-<version>.plasmoid` with `metadata.json` at the
archive root, as KDE's widget packaging documentation requires, and excludes
`*.qmlc`, `*.jsc`, and `__pycache__`. Verify the exact archive you intend to
upload before publishing:

```sh
kpackagetool6 --type Plasma/Applet --install dist/ai-limits-1.0.0.plasmoid
```

## Resolved blockers

1. ~~Move the read-only collector into `package/contents/tools/`.~~ Done.
2. ~~Resolve and invoke the bundled helper from QML using a package-local
   path.~~ Done, via `Qt.resolvedUrl`. It is run through `python3` rather than
   executed directly, because KPackage installs do not reliably preserve the
   executable bit.
3. ~~Keep provider credentials outside the plasmoid and never expose them to
   QML.~~ Unchanged and still true: only normalized numbers cross into QML.
4. ~~Provide a Claude bridge procedure that works for Store installations.~~ The
   bridge is now a fallback rather than the primary path; Claude usage is read
   live from the stored CLI login, so a Store install needs no `PATH` setup.
5. ~~Add screenshots using sample rather than personal usage data.~~
   `screenshots/widget-popup.png` is rendered from a sample
   `~/.config/limit-widget/limits.json`.

## Uploading to KDE Store

**This step cannot be automated.** KDE's OCS v1 API server exposes only read
actions — `contentdata`, `contentdownload`, `contentcategories`, `comments`,
`vote`, and person lookups. There is no content create, add, or upload action,
which matches KDE's own note that KNewStuff implements OCS Content Create on
the client but store.kde.org has no server-side support for it. Tagging a
release therefore publishes to GitHub automatically and leaves a reminder in
the run summary for this part.

The GitHub release is published by `.github/workflows/release.yml` on any `v*`
tag; the Store listing is created by hand at <https://store.kde.org/>. Sign in with a KDE Identity account, then **Add
Product**:

| Field | Value |
| --- | --- |
| Category | Plasma 6 → Plasma 6 Add-Ons → Plasma 6 Applets |
| Title | AI Limits |
| Summary | Codex, Claude Code, and GitHub Copilot usage limits in one monochrome panel widget |
| Version | 1.0.0 |
| License | GPLv3 |
| Homepage | <https://github.com/SLASHLogin/ai-limits-plasmoid> |
| File | `ai-limits-1.0.0.plasmoid` from the GitHub release |
| Screenshot | `screenshots/widget-popup.png` |

Set the file's own version to `1.0.0` too — Plasma's **Get New Widgets**
compares that field, not the product version, when offering updates.

Paste the disclosure under "Listing text" below into the description. Do not
add OpenAI's, Anthropic's, or GitHub's logos to the listing artwork itself: the
bundled icons are covered by the notices in this repository, but Store
banner artwork is marketing use and a different question.

For later versions, bump `Version` in `package/metadata.json`, rebuild with
`tools/make-store-archive.sh`, and use **Update** on the existing product
rather than creating a new one, so existing installs are offered the upgrade.

## Remaining release checks

- ~~Confirm the bundled marks may be redistributed.~~ No OpenAI brand asset is
  shipped any more; the Codex glyph is original to this project. The Claude and
  GitHub icon files are MIT and their marks are excluded from the GPL grant by
  `TRADEMARKS.md`.
- Test installation from the exact archive intended for upload, in a clean user
  account.
- Test horizontal and vertical panels, light and dark themes, offline mode,
  expired authentication, and missing CLIs.

## Listing text

Disclose in the Store description, because the Store page is where a user
decides to install:

> Usage is collected locally. The widget reads the sign-ins the Codex, Claude
> Code, and GitHub CLIs already store on your machine and contacts only the
> providers themselves. It sends no telemetry and has no server of its own.
>
> Codex and Copilot figures come from client endpoints that those vendors do
> not document as public third-party APIs, and Claude usage comes from the
> endpoint behind Claude Code's own `/usage`. Any of them may change without
> notice.

The full privacy statement is in the project README.

## Store metadata

- Name: **AI Limits**
- Applet id: **dev.slashlogin.ailimits**
- Version: **1.0.0**
- Category: **System Information**
- Plasma version: **6.0+**
- License: **GPL-3.0-or-later** for widget code; third-party marks separately attributed
- Homepage: <https://github.com/SLASHLogin/ai-limits-plasmoid>
- Issues: <https://github.com/SLASHLogin/ai-limits-plasmoid/issues>

Official references:

- KDE widget packaging: <https://develop.kde.org/docs/plasma/widget/setup/>
- KDE widget testing: <https://develop.kde.org/docs/plasma/widget/testing/>
- KDE Store: <https://store.kde.org/>
