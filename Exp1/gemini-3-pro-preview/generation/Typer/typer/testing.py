import sys
import contextlib
from io import StringIO
from .models import Exit

class Result:
    def __init__(self, exit_code, stdout, stderr, exc_info=None):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.exc_info = exc_info

class CliRunner:
    def invoke(self, app, args=None, catch_exceptions=True):
        if args is None:
            args = []
        
        stdout = StringIO()
        stderr = StringIO()
        
        exit_code = 0
        exc_info = None
        
        old_argv = sys.argv
        sys.argv = ["app"] + list(args)
        
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                try:
                    app(args)
                except SystemExit as e:
                    exit_code = e.code if isinstance(e.code, int) else 1
                except Exit as e:
                    exit_code = e.exit_code
        except Exception as e:
            if not catch_exceptions:
                raise
            exc_info = sys.exc_info()
            exit_code = 1
            stderr.write(str(e))
        finally:
            sys.argv = old_argv
            
        return Result(exit_code, stdout.getvalue(), stderr.getvalue(), exc_info)