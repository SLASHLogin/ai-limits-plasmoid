# Contributing

Patches are welcome — bug fixes, new providers, panel layouts, translations.

## Build and test

Nothing beyond Plasma 6 and Python 3 is required.

```sh
python3 tests/test_helper.py                      # collector tests
kpackagetool6 --type Plasma/Applet --install package
plasmawindowed dev.slashlogin.ailimits            # run the applet standalone
```

The test suite uses sanitized temporary configuration and never contacts a
provider. Before sending a change, please also check it by hand in a real
panel: horizontal and vertical, light and dark, and with a provider signed out.

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
