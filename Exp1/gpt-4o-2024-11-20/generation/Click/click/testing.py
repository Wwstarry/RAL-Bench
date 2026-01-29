# click/testing.py

import sys
from io import StringIO


class CliRunner:
    def __init__(self):
        self.output = None

    def invoke(self, cli, args=None, input=None, env=None):
        args = args or []
        input_stream = StringIO(input) if input else None
        output_stream = StringIO()
        sys.stdin = input_stream or sys.stdin
        sys.stdout = output_stream
        sys.stderr = output_stream

        exit_code = 0
        try:
            ctx = cli.make_context(args)
            cli.invoke(ctx)
        except Exception as e:
            exit_code = 1
            output_stream.write(str(e))
        finally:
            sys.stdin = sys.__stdin__
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

        self.output = output_stream.getvalue()
        return Result(exit_code, self.output)


class Result:
    def __init__(self, exit_code, output):
        self.exit_code = exit_code
        self.output = output