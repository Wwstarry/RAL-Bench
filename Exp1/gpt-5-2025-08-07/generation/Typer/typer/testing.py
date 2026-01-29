import sys
import io
from typing import Any, List, Optional, Tuple


class Result:
    def __init__(self, exit_code: int, stdout: str, stderr: str, exception: Optional[BaseException] = None):
        self.exit_code = int(exit_code)
        self.stdout = stdout
        self.stderr = stderr
        # In click, output is stdout. We provide alias for convenience.
        self.output = stdout
        self.exception = exception

    def __repr__(self) -> str:
        return f"<Result exit_code={self.exit_code} stdout_len={len(self.stdout)} stderr_len={len(self.stderr)}>"

class CliRunner:
    def __init__(self):
        pass

    def invoke(self, app: Any, args: Optional[List[str]] = None, input: Optional[str] = None) -> Result:
        args = list(args or [])
        # Capture stdout/stderr
        old_out = sys.stdout
        old_err = sys.stderr
        old_in = sys.stdin
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        in_buf = io.StringIO(input or "")
        sys.stdout = out_buf
        sys.stderr = err_buf
        sys.stdin = in_buf
        exit_code = 0
        exc: Optional[BaseException] = None
        try:
            # Prefer internal run method if available
            if hasattr(app, "_run"):
                exit_code, exc = app._run(args)
            elif callable(app):
                # If app is a callable like Typer, pass args
                exit_code = app(args)
            else:
                # Unknown object; cannot invoke
                err_buf.write("Error: Unable to invoke application\n")
                exit_code = 1
        except SystemExit as e:
            exit_code = e.code if isinstance(e.code, int) else 1
            exc = e
        except BaseException as e:
            # Unhandled exception
            err_buf.write(f"Error: {e}\n")
            exit_code = 1
            exc = e
        finally:
            # Restore
            sys.stdout = old_out
            sys.stderr = old_err
            sys.stdin = old_in
        return Result(exit_code, out_buf.getvalue(), err_buf.getvalue(), exc)