# Third-party notices

The widget itself is GPL-3.0-or-later. The bundled provider icons come from the
sources below.

| File | Source | License |
| --- | --- | --- |
| `codex-symbolic.svg` | OpenAI Blossom, from OpenAI's brand asset archive | OpenAI brand guidelines (not an open-source license) |
| `codex-generic-symbolic.svg` | Original to this project | GPL-3.0-or-later |
| `claude-symbolic.svg` | [Lobe Icons](https://github.com/lobehub/lobe-icons), `@lobehub/icons-static-svg` | MIT |
| `copilot-symbolic.svg` | [Primer Octicons](https://github.com/primer/octicons), `mark-github-24` | MIT |

The MIT terms are compatible with GPL-3.0-or-later, so those two files are
redistributed as part of this GPL work with their copyright notices intact.

`codex-symbolic.svg` carries no open-source license. It is OpenAI's brand
asset, shipped unmodified and used nominatively to identify whose usage the
Codex row shows. OpenAI's brand guidelines ask third parties to obtain written
consent before using their assets and not to alter the logo; this project has
not obtained that consent, and the widget draws every icon as a mask recoloured
to the desktop theme.

`codex-generic-symbolic.svg` is a neutral terminal glyph drawn for this project
and depicts no one's mark. A distribution that would rather not carry OpenAI's
asset can use it instead: the applet takes each provider's icon filename from
the `symbol` field in the collector's output, so swapping it needs no code
change.

## Trademarks

The marks these files depict are trademarks of their owners and are **not**
covered by this project's GPL grant. See [`TRADEMARKS.md`](TRADEMARKS.md) for
the full notice, made as an additional term under GPL-3.0 section 7(e).
