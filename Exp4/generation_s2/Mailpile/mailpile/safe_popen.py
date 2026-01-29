import os
import subprocess
import threading
from typing import Optional, Sequence, Union


def _to_bytes(data):
    if data is None:
        return None
    if isinstance(data, bytes):
        return data
    return str(data).encode("utf-8", "replace")


def _to_text(data):
    if data is None:
        return None
    if isinstance(data, str):
        return data
    return data.decode("utf-8", "replace")


class SafePopen(subprocess.Popen):
    """
    Small wrapper around subprocess.Popen with convenience helpers and safe
    defaults: no shell by default, close_fds, and optional text-mode I/O.
    """

    def __init__(
        self,
        args: Union[str, Sequence[str]],
        stdin=None,
        stdout=None,
        stderr=None,
        shell: bool = False,
        close_fds: bool = True,
        env: Optional[dict] = None,
        cwd: Optional[str] = None,
        text: bool = False,
        **kwargs,
    ):
        self._text_mode = bool(text)
        super().__init__(
            args,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            shell=shell,
            close_fds=close_fds,
            env=env,
            cwd=cwd,
            **kwargs,
        )

    def communicate(self, input=None, timeout=None):
        if self._text_mode and isinstance(input, str):
            input = _to_bytes(input)
        out, err = super().communicate(input=input, timeout=timeout)
        if self._text_mode:
            out = _to_text(out)
            err = _to_text(err)
        return out, err


def safe_popen(*args, **kwargs) -> SafePopen:
    return SafePopen(*args, **kwargs)


def safe_popen_get_output(
    args: Union[str, Sequence[str]],
    input_data: Optional[Union[str, bytes]] = None,
    env: Optional[dict] = None,
    cwd: Optional[str] = None,
    timeout: Optional[float] = None,
    text: bool = True,
) -> str:
    """
    Run a subprocess and return stdout (decoded if text=True). Raises CalledProcessError on failure.
    """
    p = SafePopen(
        args,
        stdin=subprocess.PIPE if input_data is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=cwd,
        text=False,
    )
    out, err = p.communicate(input=_to_bytes(input_data), timeout=timeout)
    rc = p.returncode
    if rc != 0:
        e = subprocess.CalledProcessError(rc, args, output=out, stderr=err)
        raise e
    if text:
        return _to_text(out or b"")
    return out or b""


class PipeReader(threading.Thread):
    """
    Helper thread which reads from a file-like object until EOF.
    """

    def __init__(self, fd, collect: bool = True):
        super().__init__(daemon=True)
        self.fd = fd
        self.collect = collect
        self.data = b""
        self._done = threading.Event()

    def run(self):
        try:
            chunks = []
            while True:
                buf = self.fd.read(8192)
                if not buf:
                    break
                if self.collect:
                    chunks.append(buf)
            if self.collect:
                self.data = b"".join(chunks)
        finally:
            self._done.set()

    def join_and_get(self, timeout: Optional[float] = None) -> bytes:
        self.join(timeout=timeout)
        return self.data


def pipe(*cmd, input_data: Optional[Union[str, bytes]] = None, env=None, cwd=None) -> bytes:
    """
    Run a command and return raw stdout bytes. Convenience wrapper.
    """
    return safe_popen_get_output(list(cmd), input_data=input_data, env=env, cwd=cwd, text=False)