#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 SLASHLogin
# SPDX-License-Identifier: GPL-3.0-or-later
"""Print the CHANGELOG body for one version, for use as release notes.

A sed range from one "## " heading to the next cannot express "to the next
heading or end of file": at the end of the file the range runs to EOF and
deleting the last line eats a real line of the entry instead of the heading
that is not there. The newest entry sits at the top and so has a following
heading, but the oldest does not, which is exactly the case a first release
hits.
"""

import sys
from pathlib import Path


def section(text: str, version: str) -> str:
    wanted = f"## {version}"
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == wanted)
    except StopIteration:
        return ""
    body = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        body.append(line)
    return "\n".join(body).strip("\n")


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: changelog-section.py <CHANGELOG.md> <version>", file=sys.stderr)
        return 2
    body = section(Path(argv[1]).read_text(encoding="utf-8"), argv[2])
    if not body:
        return 1
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
