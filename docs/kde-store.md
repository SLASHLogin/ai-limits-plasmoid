# KDE Store publication assessment

## Recommendation

Do not publish the current `0.9.0` package to KDE Store yet. The GitHub source
release is usable, but a Store installation would install only the plasmoid
KPackage and would not run this repository's CMake installer.

## Blocking issue

The applet currently invokes `limit-widget-helper --json`. CMake installs that
helper, the Claude status-line bridge, and the setup utility into
`~/.local/bin`. KDE Store installs the contents of `package/` under Plasma's
plasmoid directory; it does not install those external executables.

Before Store publication, make the downloadable plasmoid self-contained:

1. Move or copy the read-only collector into `package/contents/tools/`.
2. Resolve and invoke that bundled helper from QML using its package-local path.
3. Keep provider credentials outside the plasmoid and never expose them to QML.
4. Provide a clear Claude bridge procedure that works for Store installations,
   where `limit-widget-setup` is not automatically placed on `PATH`.
5. Test installation from the exact archive intended for upload in a clean
   user account.

## Other release checks

- Confirm that OpenAI, Claude, and GitHub marks may be redistributed in the
  uploaded package and retain `THIRD_PARTY_NOTICES.md` in the release source.
- Clearly disclose that the Codex and Copilot collectors use client/internal
  endpoints which may change without notice.
- Add screenshots using sample rather than personal usage data.
- Test horizontal and vertical panels, light and dark themes, offline mode,
  expired authentication, and missing CLIs.
- Add a privacy statement explaining that collection is local and identifying
  the endpoints contacted.
- Build the upload archive from the contents of `package/`, with
  `metadata.json` at the archive root, as described by KDE's widget setup docs.

## Tentative Store metadata

- Name: **AI Limits**
- Category: **System Information**
- Plasma version: **6.0+**
- License: **MIT** for widget code; third-party marks separately attributed
- Homepage: <https://github.com/SLASHLogin/ai-limits-plasmoid>
- Issues: <https://github.com/SLASHLogin/ai-limits-plasmoid/issues>

Official references:

- KDE widget packaging: <https://develop.kde.org/docs/plasma/widget/setup/>
- KDE widget testing: <https://develop.kde.org/docs/plasma/widget/testing/>
- KDE Store: <https://store.kde.org/>
