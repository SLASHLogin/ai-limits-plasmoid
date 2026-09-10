#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 SLASHLogin
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Run the whole suite with outbound network access blocked, so a test that
# would have contacted OpenAI, Anthropic, or GitHub fails instead of quietly
# succeeding against a real account.
#
# Two guards are needed, because the collector reaches the network two ways:
#   sitecustomize.py  blocks AF_INET/AF_INET6 sockets in every Python process,
#                     including the collector subprocesses the tests spawn;
#   bin/gh            shadows the real gh, which is a Go binary and so is not
#                     affected by the Python guard at all.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"

export PYTHONPATH="$here/nonet${PYTHONPATH:+:$PYTHONPATH}"
export PATH="$here/nonet/bin:$PATH"

status=0
for suite in "$here/test_helper.py" "$here/test_vendor_parsing.py"; do
    echo "== $(basename "$suite")"
    python3 "$suite" || status=1
done

echo "== verifying the guard is actually armed"
python3 - <<'PY'
import socket, sys
try:
    socket.create_connection(("example.com", 443), timeout=3)
except OSError as error:
    if type(error).__name__ != "NetworkAccessDenied":
        sys.exit(f"network blocked, but by {type(error).__name__}, not the guard")
    print("   guard armed: outbound sockets refused")
else:
    sys.exit("   GUARD NOT ARMED: an outbound connection succeeded")
PY

if ! command -v gh >/dev/null || gh api copilot_internal/user >/dev/null 2>&1; then
    echo "   GH STUB NOT ARMED: real gh is reachable" >&2
    exit 1
fi
echo "   gh stub armed: Copilot cannot be queried"

exit $status
