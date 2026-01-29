import os
import subprocess
from typing import Iterable, Optional, Tuple, Union


def make_pipe():
    """Create an OS pipe and try to mark fds close-on-exec where supported."""
    r, w = os.pipe()
    for fd in (r, w):
        try:
            os.set_inheritable(fd, False)
        except Exception:
            pass
    return r, w


def SafePopen(args, *popenargs, **kwargs) -> subprocess.Popen:
    """
    Safer wrapper around subprocess.Popen.

    Defaults:
      - close_fds=True (where supported)
      - shell=False (unless explicitly requested)
    """
    if "close_fds" not in kwargs:
        kwargs["close_fds"] = True
    if "shell" not in kwargs:
        kwargs["shell"] = False
    return subprocess.Popen(args, *popenargs, **kwargs)


# Backwards compatible alias
safe_popen = SafePopen


def _decode_output(data: Optional[bytes], encoding: str = "utf-8") -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        # Shouldn't happen with our usage, but be tolerant.
        s = data
    else:
        s = data.decode(encoding, "replace")
    # Normalize Windows newlines to Unix newlines for stable tests/output.
    return s.replace("\r\n", "\n").replace("\r", "\n")


def backtick(
    command: Union[str, Iterable[str]],
    timeout: Optional[float] = None,
    input: Optional[Union[str, bytes]] = None,
    encoding: str = "utf-8",
) -> Tuple[int, str, str]:
    """
    Run a command and capture (rc, stdout, stderr) as text.

    Newlines are normalized to '\\n' to avoid platform-specific differences.
    """
    stdin_data = None
    if input is not None:
        if isinstance(input, bytes):
            stdin_data = input
        else:
            stdin_data = str(input).encode(encoding, "replace")

    if timeout is not None:
        cp = subprocess.run(
            command,
            input=stdin_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            shell=False,
            close_fds=True,
        )
        rc = int(cp.returncode)
        out = _decode_output(cp.stdout, encoding=encoding)
        err = _decode_output(cp.stderr, encoding=encoding)
        return rc, out, err

    p = SafePopen(
        command,
        stdin=subprocess.PIPE if input is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out_b, err_b = p.communicate(stdin_data)
    rc = int(p.returncode) if p.returncode is not None else 0
    out = _decode_output(out_b, encoding=encoding)
    err = _decode_output(err_b, encoding=encoding)
    return rc, out, err