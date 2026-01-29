import os
import subprocess
from typing import Iterator, List, Tuple, Optional


class Safe_Popen(subprocess.Popen):
    """
    A thin wrapper around subprocess.Popen with safer defaults.

    - shell defaults to False (never implicitly enabled)
    - close_fds defaults to True where supported (POSIX)
    """

    def __init__(self, args, *popenargs, **kwargs):
        # Never implicitly enable shell=True
        kwargs.setdefault('shell', False)

        # Safer default on POSIX; on Windows close_fds has constraints when
        # redirecting handles. Let caller override if needed.
        if os.name == 'posix':
            kwargs.setdefault('close_fds', True)

        # Support subprocess.run-like "check=" kwarg without breaking Popen init
        self._check = bool(kwargs.pop('check', False))

        super().__init__(args, *popenargs, **kwargs)

    def communicate(self, input=None, **kwargs):
        out, err = super().communicate(input=input, **kwargs)
        if self._check:
            rc = self.poll()
            if rc:
                raise subprocess.CalledProcessError(rc, self.args, output=out, stderr=err)
        return out, err


def safe_popen(*args, **kwargs) -> Safe_Popen:
    """
    Convenience wrapper returning a Safe_Popen instance.
    """
    return Safe_Popen(*args, **kwargs)


def make_pipes(n: int = 2) -> List[Tuple[int, int]]:
    pipes = []
    for _ in range(int(n)):
        r, w = os.pipe()
        pipes.append((r, w))
    return pipes


def close_pipes(pipes) -> None:
    if not pipes:
        return
    for p in pipes:
        if not p:
            continue
        for fd in p:
            if fd is None:
                continue
            try:
                os.close(fd)
            except OSError:
                pass


def pipe_reader(fd, decode: bool = True, encoding: str = 'utf-8', errors: str = 'replace') -> Iterator:
    """
    Yield lines from an OS-level file descriptor until EOF.

    If decode=True yields str, else yields bytes.
    Closes the file descriptor when done.
    """
    f = None
    try:
        # Use binary mode always; decode per-line if requested.
        f = os.fdopen(fd, 'rb', closefd=True)
        for line in f:
            if decode:
                yield line.decode(encoding, errors)
            else:
                yield line
    finally:
        # fdopen with closefd=True should close automatically, but be explicit.
        try:
            if f is not None:
                f.close()
        except Exception:
            pass