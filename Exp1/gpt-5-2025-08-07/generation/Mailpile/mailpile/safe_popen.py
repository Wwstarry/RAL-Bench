"""
Safe subprocess wrapper and pipe helpers.

This module provides a minimal, safe API around subprocess to avoid
misuse of shell=True and to simplify common patterns.
"""

import os
import shlex
import subprocess
from typing import Iterable, Optional, Tuple


class SafePopen:
    """
    Wrapper around subprocess.Popen that enforces shell=False and reasonable defaults.
    Provides context manager support and convenience methods.
    """

    def __init__(self,
                 cmd,
                 args: Optional[Iterable[str]] = None,
                 stdin=None,
                 stdout=subprocess.PIPE,
                 stderr=subprocess.PIPE,
                 env: Optional[dict] = None,
                 cwd: Optional[str] = None,
                 text: bool = True):
        argv = _normalize_argv(cmd, args)
        self._proc = subprocess.Popen(
            argv,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            env=_sanitize_env(env),
            cwd=cwd,
            shell=False,
            close_fds=True,
            text=text
        )

    def communicate(self, input=None, timeout: Optional[float] = None) -> Tuple[str, str]:
        out, err = self._proc.communicate(input=input, timeout=timeout)
        return out, err

    @property
    def returncode(self) -> Optional[int]:
        return self._proc.returncode

    def poll(self) -> Optional[int]:
        return self._proc.poll()

    def wait(self, timeout: Optional[float] = None) -> int:
        return self._proc.wait(timeout=timeout)

    def kill(self):
        self._proc.kill()

    def terminate(self):
        self._proc.terminate()

    @property
    def stdin(self):
        return self._proc.stdin

    @property
    def stdout(self):
        return self._proc.stdout

    @property
    def stderr(self):
        return self._proc.stderr

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        # Ensure the process resources are cleaned up
        try:
            if self._proc.stdin and not self._proc.stdin.closed:
                self._proc.stdin.close()
        except Exception:
            pass
        try:
            if self._proc.stdout and not self._proc.stdout.closed:
                self._proc.stdout.close()
        except Exception:
            pass
        try:
            if self._proc.stderr and not self._proc.stderr.closed:
                self._proc.stderr.close()
        except Exception:
            pass
        try:
            if self._proc.poll() is None:
                self._proc.terminate()
        except Exception:
            pass
        return False  # don't suppress exceptions


def _normalize_argv(cmd, args: Optional[Iterable[str]] = None):
    """
    Normalize command and args to a list suitable for shell=False executables.
    Raises ValueError for suspicious command strings.
    """
    if isinstance(cmd, str):
        # Disallow shell metacharacters in a single string command
        if any(ch in cmd for ch in ["|", "&", ";", "`", "$(", ")", "<", ">", "*"]):
            raise ValueError("Unsafe command string; provide a list of arguments")
        argv = shlex.split(cmd)
    elif isinstance(cmd, Iterable):
        argv = list(cmd)
    else:
        raise TypeError("cmd must be str or iterable of strings")

    if args:
        argv.extend(list(args))
    if not argv or not isinstance(argv[0], str) or not argv[0]:
        raise ValueError("Invalid command")
    # Ensure all args are strings
    argv = [str(a) for a in argv]
    return argv


def _sanitize_env(env: Optional[dict]):
    if env is None:
        return None
    clean_env = {}
    for k, v in env.items():
        clean_env[str(k)] = str(v)
    return clean_env


def run(cmd,
        args: Optional[Iterable[str]] = None,
        input_data: Optional[str] = None,
        timeout: Optional[float] = None,
        env: Optional[dict] = None,
        cwd: Optional[str] = None,
        text: bool = True) -> Tuple[int, str, str]:
    """
    Run a command safely, capturing stdout/stderr and returning (rc, out, err).
    """
    argv = _normalize_argv(cmd, args)
    try:
        completed = subprocess.run(
            argv,
            input=input_data,
            capture_output=True,
            timeout=timeout,
            env=_sanitize_env(env),
            cwd=cwd,
            shell=False,
            text=text,
        )
        return completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as te:
        # On timeout, return code 124 (common for timeout) and any partial output
        return 124, te.stdout or "", te.stderr or ""


def open_pipe_reader(cmd,
                     args: Optional[Iterable[str]] = None,
                     env: Optional[dict] = None,
                     cwd: Optional[str] = None,
                     text: bool = True):
    """
    Open a pipe for reading from a subprocess's stdout.
    Returns (proc, reader).
    """
    proc = SafePopen(cmd, args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                     env=env, cwd=cwd, text=text)
    return proc, proc.stdout


def open_pipe_writer(cmd,
                     args: Optional[Iterable[str]] = None,
                     env: Optional[dict] = None,
                     cwd: Optional[str] = None,
                     text: bool = True):
    """
    Open a pipe for writing to a subprocess's stdin.
    Returns (proc, writer).
    """
    proc = SafePopen(cmd, args=args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, env=env, cwd=cwd, text=text)
    return proc, proc.stdin


# Convenience alias to mimic Popen usage
Popen = SafePopen

__all__ = [
    "SafePopen",
    "Popen",
    "run",
    "open_pipe_reader",
    "open_pipe_writer",
]