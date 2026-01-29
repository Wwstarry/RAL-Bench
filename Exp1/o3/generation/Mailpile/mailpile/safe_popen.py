"""
mailpile.safe_popen
===================

A *very* small wrapper around :class:`subprocess.Popen` whose sole
purpose, in the context of this kata, is to

1.  Make spawning sub-processes a little less verbose.
2.  Enforce sane defaults such as ``close_fds=True`` so we do not leak
    file descriptors in forking web servers (as the real Mailpile takes
    care to avoid).

Only the happy-path is implemented; advanced features present in the
upstream implementation (signal handling, resource limits, …) are
outside the scope of these tests.
"""
from __future__ import unicode_literals, absolute_import

import subprocess
import sys
from typing import Iterable, List, Mapping, Sequence, Tuple, Union, Optional

__all__ = [
    "SafePopen",
    "run",
]

# Typing helpers
Cmd = Union[str, Sequence[str]]


class SafePopen(subprocess.Popen):
    """
    A thin wrapper around :class:`subprocess.Popen` which adjusts the
    default arguments to more secure values.

    Apart from that it behaves exactly like its superclass.
    """

    def __init__(self,
                 args: Cmd,
                 stdin: Optional[int] = subprocess.PIPE,
                 stdout: Optional[int] = subprocess.PIPE,
                 stderr: Optional[int] = subprocess.PIPE,
                 shell: bool = False,
                 text: bool = True,
                 **kwargs):
        # Ensure we do not leak file descriptors into child processes.
        kwargs.setdefault("close_fds", True)

        # Ensure we get *text* (str) instead of bytes by default – this is
        # what the tests expect and matches Python 3's `text=True` flag.
        kwargs.setdefault("text", text)

        super(SafePopen, self).__init__(
            args=args,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            shell=shell,
            **kwargs
        )


def run(command: Cmd,
        input_data: Union[str, bytes, None] = None,
        check: bool = True,
        **kwargs) -> Tuple[str, str]:
    """
    Convenience helper that starts a process, waits for it to finish and
    returns *(stdout, stderr)*.  If *check* is true and the return code
    is non-zero a :class:`subprocess.CalledProcessError` is raised.

    Example
    -------
    >>> out, err = run(['echo', 'hello'])
    >>> out.strip()
    'hello'
    """
    proc = SafePopen(command, **kwargs)
    stdout, stderr = proc.communicate(input=input_data)

    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(
            proc.returncode, command, output=stdout, stderr=stderr
        )
    return stdout, stderr