#!/usr/bin/env bash
# Build the .plasmoid archive for KDE Store upload.
#
# KDE expects metadata.json at the archive root, so the archive is built from
# the *contents* of package/ rather than from the directory itself. Python's
# zipfile is used instead of zip(1) so the only tool needed is the Python 3
# the widget already requires.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$root" <<'PY'
import json, pathlib, sys, zipfile

root = pathlib.Path(sys.argv[1])
package = root / "package"
version = json.loads((package / "metadata.json").read_text())["KPlugin"]["Version"]

out = root / "dist" / f"ai-limits-{version}.plasmoid"
out.parent.mkdir(parents=True, exist_ok=True)
out.unlink(missing_ok=True)

SKIP_SUFFIX = {".qmlc", ".jsc"}
SKIP_NAME = {".DS_Store"}

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(package.rglob("*")):
        if not path.is_file():
            continue
        # Build leftovers and editor droppings do not belong in a published archive.
        if path.suffix in SKIP_SUFFIX or path.name in SKIP_NAME:
            continue
        if "__pycache__" in path.parts:
            continue
        archive.write(path, path.relative_to(package))

print(f"built {out}")
for name in zipfile.ZipFile(out).namelist():
    print(f"  {name}")
PY
