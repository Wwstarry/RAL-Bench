import io
import sys
from typing import Optional


class StdSim(io.TextIOBase):
    """
    A very simple in-memory text stream that behaves like a file-like object.
    Useful for capturing output during transcript tests.

    - write(str): append to buffer
    - flush(): no-op
    - getvalue(): returns entire buffer
    - clear(): empties buffer
    """

    def __init__(self):
        super().__init__()
        self._buffer = []

    def writable(self):
        return True

    def write(self, s: str) -> int:
        if s is None:
            return 0
        if not isinstance(s, str):
            s = str(s)
        self._buffer.append(s)
        return len(s)

    def flush(self):
        # No operation needed for in-memory buffer
        pass

    def getvalue(self) -> str:
        return "".join(self._buffer)

    def clear(self):
        self._buffer = []

    def close(self):
        # Allow text IO interface to close; does not lose buffer
        super().close()


def strip_quotes(s: str) -> str:
    """Remove symmetric single or double quotes from the ends of the string."""
    if not s:
        return s
    if len(s) >= 2 and ((s[0] == s[-1] == "'") or (s[0] == s[-1] == '"')):
        return s[1:-1]
    return s


def quote_string(s: str, prefer_double: bool = True) -> str:
    """
    Quote a string if necessary (contains whitespace or shell-sensitive chars).
    Keeps existing quoting if already present.

    Examples:
        quote_string('hello') -> 'hello'
        quote_string('hello world') -> '"hello world"'
    """
    if not isinstance(s, str):
        s = str(s)
    if not s:
        return '""' if prefer_double else "''"

    has_ws = any(ch.isspace() for ch in s)
    special = set('|&;<>()$`\\*"\'')
    needs_quote = has_ws or any(ch in special for ch in s)

    if needs_quote:
        if prefer_double:
            return f'"{s}"'
        else:
            return f"'{s}'"
    return s


class OutputCapture:
    """
    Context manager that captures sys.stdout and sys.stderr. Optionally also updates
    a cmd-like object's stdout/stderr attributes to the same streams during capture.

    Usage:
        with OutputCapture(self) as cap:
            self.onecmd("help")
        print(cap.stdout_lines)
    """

    def __init__(self, cmd_obj: Optional[object] = None):
        self.cmd_obj = cmd_obj
        self._old_sys_stdout = None
        self._old_sys_stderr = None
        self._old_cmd_stdout = None
        self._old_cmd_stderr = None
        self.stdout_sim = StdSim()
        self.stderr_sim = StdSim()

    def __enter__(self):
        self._old_sys_stdout = sys.stdout
        self._old_sys_stderr = sys.stderr
        sys.stdout = self.stdout_sim
        sys.stderr = self.stderr_sim
        if self.cmd_obj is not None:
            self._old_cmd_stdout = getattr(self.cmd_obj, "stdout", None)
            self._old_cmd_stderr = getattr(self.cmd_obj, "stderr", None)
            try:
                self.cmd_obj.stdout = self.stdout_sim
            except Exception:
                pass
            try:
                self.cmd_obj.stderr = self.stderr_sim
            except Exception:
                pass
        return self

    def __exit__(self, exc_type, exc, tb):
        sys.stdout = self._old_sys_stdout
        sys.stderr = self._old_sys_stderr
        if self.cmd_obj is not None:
            if self._old_cmd_stdout is not None:
                self.cmd_obj.stdout = self._old_cmd_stdout
            if self._old_cmd_stderr is not None:
                self.cmd_obj.stderr = self._old_cmd_stderr
        return False  # do not suppress exceptions

    @property
    def stdout_text(self) -> str:
        return self.stdout_sim.getvalue()

    @property
    def stderr_text(self) -> str:
        return self.stderr_sim.getvalue()

    @property
    def stdout_lines(self):
        return split_output_lines(self.stdout_text)

    @property
    def stderr_lines(self):
        return split_output_lines(self.stderr_text)


def split_output_lines(buf: str):
    """
    Split output into lines in a transcript-friendly way:
    - Normalize trailing newline by splitting on '\n'
    - Preserve empty lines
    - Strip trailing '\r' if present (Windows compatibility)
    """
    if buf is None or buf == "":
        return []
    lines = buf.split("\n")
    # Remove trailing carriage returns if present
    return [line[:-1] if line.endswith("\r") else line for line in lines]