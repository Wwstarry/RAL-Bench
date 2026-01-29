import sys
from io import StringIO
from typing import List, Optional, Tuple

from ..core import Typer
from ..main import Exit


class CliRunner:
    def __init__(self):
        self.stdout = StringIO()
        self.stderr = StringIO()

    def invoke(
        self,
        app: Typer,
        args: Optional[List[str]] = None,
        catch_exceptions: bool = True,
    ) -> Tuple[int, str, str]:
        if args is None:
            args = []

        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        
        exit_code = 0
        try:
            app.run(args)
        except Exit as e:
            exit_code = e.exit_code
        except Exception as e:
            if not catch_exceptions:
                raise
            exit_code = 1
            self.stderr.write(f"Error: {e}")
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
        
        stdout_output = self.stdout.getvalue()
        stderr_output = self.stderr.getvalue()
        
        self.stdout = StringIO()
        self.stderr = StringIO()
        
        return exit_code, stdout_output, stderr_output