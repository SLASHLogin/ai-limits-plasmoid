# Trademark notice

**The provider logos in this repository are not covered by the GPL.**

This notice is an additional term under section 7(e) of the GNU General Public
License version 3, which permits "declining to grant rights under trademark law
for use of some trade names, trademarks, or service marks." It is therefore not
a "further restriction" under section 10, and it does not affect your GPL rights
in the widget's source code.

## What the GPL grant covers

The GPL-3.0-or-later grant in [`LICENSE`](LICENSE) applies to the source code of
this project: the QML, the Python collector, the build files, and the
documentation.

It does **not** grant any right to use the trademarks, service marks, trade
names, or logos of OpenAI, Anthropic, or GitHub. Those belong to their
respective owners, and no such right is or can be granted here, because this
project does not hold them.

## Files this applies to

| File | Mark | Owner |
| --- | --- | --- |
| `package/contents/icons/claude-symbolic.svg` | Claude mark | Anthropic |
| `package/contents/icons/copilot-symbolic.svg` | GitHub mark | GitHub, Inc. |

`codex-symbolic.svg` depicts no one's mark. It is a generic terminal glyph
drawn for this project and is covered by the GPL like any other source file.

The `claude-symbolic.svg` and `copilot-symbolic.svg` **files** are redistributed
under the MIT license of the icon sets they come from (Lobe Icons and Primer
Octicons); see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). MIT grants
copyright permission in the file. It does not grant trademark permission in the
mark the file depicts. Those are separate questions and this notice concerns the
second one.

No OpenAI brand asset is bundled. OpenAI's brand guidelines require prior
written consent for third-party use of their assets and prohibit modifying the
logo, so the Codex row uses a generic glyph instead.

## Why the marks are here

Each mark identifies which service the usage figure beside it refers to — a
nominative use. This project is not affiliated with, endorsed by, sponsored by,
or certified by OpenAI, Anthropic, or GitHub, and nothing here should be read to
suggest otherwise.

## If you fork or redistribute this

Your GPL rights in the code do not extend to the logos. If you distribute a
modified version, especially under a different name, you are responsible for
your own trademark position. In particular:

- Anthropic and GitHub publish brand guidelines covering their marks. Note that
  this widget renders every icon as a mask recolored to the desktop theme's
  text color, which is a change in appearance even though the shipped files are
  unmodified.
- Do not substitute OpenAI's Blossom for the generic Codex glyph. Their brand
  guidelines require prior written consent and prohibit modifying the logo.

The safe course for a fork is to replace the provider logos with your own
neutral glyphs. The widget reads each provider's icon filename from the
`symbol` field in the collector's output, so substituting them needs no code
change.
