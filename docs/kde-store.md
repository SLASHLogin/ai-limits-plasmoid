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

## Remaining release checks

- Confirm that OpenAI, Claude, and GitHub marks may be redistributed in the
  uploaded package and retain `THIRD_PARTY_NOTICES.md` in the release source.
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
- License: **MIT** for widget code; third-party marks separately attributed
- Homepage: <https://github.com/SLASHLogin/ai-limits-plasmoid>
- Issues: <https://github.com/SLASHLogin/ai-limits-plasmoid/issues>

Official references:

- KDE widget packaging: <https://develop.kde.org/docs/plasma/widget/setup/>
- KDE widget testing: <https://develop.kde.org/docs/plasma/widget/testing/>
- KDE Store: <https://store.kde.org/>
