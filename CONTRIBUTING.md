# Contributing

Patches are welcome — bug fixes, new providers, panel layouts, translations.

## Build and test

Nothing beyond Plasma 6 and Python 3 is required.

```sh
./tests/run-offline.sh                            # the whole suite, network blocked
kpackagetool6 --type Plasma/Applet --install package
plasmawindowed dev.slashlogin.ailimits            # run the applet standalone
```

Use `run-offline.sh` rather than calling the suites directly. It blocks
outbound sockets in every Python process — including the collector
subprocesses the tests spawn — and shadows `gh`, which is a Go binary the
Python guard cannot reach. It then fails if either guard is not armed. This is
what stops a test quietly passing against your own live account and then
behaving differently for everyone else.

Vendor responses are parsed from recorded fixtures in `tests/fixtures/`, so
`tests/test_vendor_parsing.py` covers the response handling that used to be
reachable only with a real subscription. If you add a provider or change how a
payload is read, add a fixture rather than a live request.

Before sending a change, please also check it by hand in a real panel:
horizontal and vertical, light and dark, and with a provider signed out.

## What CI checks

Every pull request runs, with a read-only token and no access to repository
secrets:

- the collector tests via `run-offline.sh`, so CI holds no credentials and
  provably cannot contact OpenAI, Anthropic, or GitHub from your patch;
- `metadata.json` and `main.xml` validity, and that the declared licence is
  still GPL-3.0-or-later;
- an SPDX header on every source file;
- a scan of your diff for credentials and for real home-directory paths — if it
  fires, rotate the credential first, then rewrite the branch;
- a DCO sign-off on each commit;
- a build of the Store archive, attached to the run as a downloadable
  artifact so a reviewer can install your change without building it.

None of these post comments or write to the repository.

## Scope

The collector reads sign-ins that the vendor CLIs already store. It does not
scrape dashboards, read browser cookies, or ask for credentials of its own, and
credentials never cross into QML — only normalized numbers do. Changes that
would break those properties will not be merged.

An unknown value must stay `—`. Never substitute zero for "we could not read
it": the whole point of the widget is to be trustworthy at a glance.

## Adding a provider

1. Add a spec to `PROVIDERS` in `package/contents/tools/limit-widget-helper`.
2. Return windows through `normalize_window`, with `unit` set to `percent` or
   `count` so the applet knows how to render them.
3. Add a symbolic 24px SVG to `package/contents/icons/` and record its source
   and license in `THIRD_PARTY_NOTICES.md`.
4. Cover the new source in `tests/test_helper.py` with a fixture, not a live
   request.

## Sign your work

This project uses the [Developer Certificate of Origin](https://developercertificate.org/).
It is not a copyright assignment — you keep the copyright in your contribution.
It is a statement that you wrote the patch, or otherwise have the right to
submit it under the project's license.

Add a sign-off line to each commit:

```sh
git commit -s
```

which appends:

```
Signed-off-by: Your Name <your.email@example.com>
```

Use a real name and a real address. By signing off you certify the DCO, quoted
in full in [`DCO`](DCO).

## License

Contributions are accepted under **GPL-3.0-or-later**, the project's license.
New files should carry:

```
SPDX-FileCopyrightText: <year> <your name>
SPDX-License-Identifier: GPL-3.0-or-later
```
