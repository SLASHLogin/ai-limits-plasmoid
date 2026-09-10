# SPDX-FileCopyrightText: 2026 SLASHLogin
# SPDX-License-Identifier: GPL-3.0-or-later
"""Refuse every outbound socket in the interpreter that imports this.

Python imports `sitecustomize` automatically at startup, so putting this
directory on PYTHONPATH arms the guard in the test process *and* in the
collector subprocesses the tests spawn — which is where a real request would
otherwise be made.

The point is not to make the tests pass. It is to make a test that would have
contacted OpenAI, Anthropic, or GitHub fail loudly instead of quietly
succeeding on a developer's machine and quietly leaking from CI.
"""

import socket


class NetworkAccessDenied(OSError):
    """Deliberately an OSError.

    urllib reports a refused connection as OSError/URLError, and the collector
    handles that by reporting an explicit error state. Raising something
    outside that hierarchy would make the collector crash on a path that in
    production degrades cleanly, so the guard would be testing its own
    exception type rather than the program.
    """


def _denied(*args, **kwargs):
    raise NetworkAccessDenied(
        "outbound network access is blocked in the test environment; "
        "use a fixture from tests/fixtures/ instead of a live request"
    )


# AF_UNIX stays available: it is local IPC, not egress, and blocking it breaks
# unrelated machinery such as DNS resolvers and subprocess plumbing.
_real_socket = socket.socket


class _GuardedSocket(_real_socket):
    def __init__(self, family=socket.AF_INET, *args, **kwargs):
        if family in (socket.AF_INET, socket.AF_INET6):
            _denied()
        super().__init__(family, *args, **kwargs)


socket.socket = _GuardedSocket
socket.create_connection = _denied
socket.create_server = _denied
