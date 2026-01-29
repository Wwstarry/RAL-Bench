import io
import textwrap
from pathlib import Path

import pytest

import cmd2
from cmd2 import Cmd2, Statement, parse_statement
from cmd2.exceptions import Cmd2ArgparseError
from cmd2.cmd2 import Cmd2ArgumentParser
from cmd2.transcript import TranscriptRunner


class App(Cmd2):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prompt = "> "

    def do_echo(self, arg):
        """Echo the arguments."""
        self.poutput(arg)

    def do_fail(self, arg):
        raise RuntimeError("boom")

    def do_quit(self, arg):
        return True

    def do_args(self, arg):
        parser = Cmd2ArgumentParser(prog="args")
        parser.add_argument("x")
        ns = self.parse_args(parser, arg)
        self.poutput(f"x={ns.x}")


def test_imports_and_public_api():
    assert hasattr(cmd2, "Cmd2")
    assert hasattr(cmd2, "Statement")
    assert cmd2.__version__


def test_parse_statement_quotes():
    st = parse_statement('cmd "a b" c')
    assert isinstance(st, Statement)
    assert st.command == "cmd"
    assert st.arg_list == ["a b", "c"]
    assert st.raw == 'cmd "a b" c'


def test_command_dispatch_and_unknown(capsys):
    out = io.StringIO()
    err = io.StringIO()
    app = App(stdout=out, stderr=err)

    app.onecmd("echo hi")
    assert out.getvalue().splitlines()[-1] == "hi"

    app.onecmd("doesnotexist 1 2")
    assert "*** Unknown syntax:" in err.getvalue()
    assert "doesnotexist 1 2" in err.getvalue()


def test_emptyline_does_not_repeat():
    out = io.StringIO()
    err = io.StringIO()
    app = App(stdout=out, stderr=err)
    app.onecmd("echo hi")
    before = out.getvalue()
    app.onecmd("")  # should not repeat
    after = out.getvalue()
    assert after == before


def test_help_lists_commands_deterministically():
    out = io.StringIO()
    err = io.StringIO()
    app = App(stdout=out, stderr=err)

    app.onecmd("help")
    lines = [ln.strip() for ln in out.getvalue().splitlines() if ln.strip()]
    # at least these exist
    for name in ["args", "echo", "fail", "help", "quit"]:
        assert name in lines
    assert lines == sorted(lines)


def test_help_for_command_uses_docstring():
    out = io.StringIO()
    err = io.StringIO()
    app = App(stdout=out, stderr=err)

    app.onecmd("help echo")
    assert "Echo the arguments." in out.getvalue()


def test_argparse_missing_arg_raises():
    app = App(stdout=io.StringIO(), stderr=io.StringIO())
    parser = Cmd2ArgumentParser(prog="t")
    parser.add_argument("x")
    with pytest.raises(Cmd2ArgparseError):
        app.parse_args(parser, "")


def test_capture_output_context_manager():
    from cmd2.utils import capture_output

    with capture_output() as (out, err):
        print("A")
        print("B", file=sys.stderr)
    assert out.getvalue().strip() == "A"
    assert err.getvalue().strip() == "B"


def test_transcript_runner_pass_and_fail(tmp_path: Path):
    out = io.StringIO()
    err = io.StringIO()
    app = App(stdout=out, stderr=err)
    tr_path = tmp_path / "t.transcript"
    tr_path.write_text(
        textwrap.dedent(
            """\
            > echo hi
            hi
            > doesnotexist
            *** Unknown syntax: doesnotexist
            """
        ),
        encoding="utf-8",
    )
    runner = TranscriptRunner(app, prompt="> ")
    res = runner.run(tr_path)
    assert res.passed, f"failures: {res.failures}"

    tr_path2 = tmp_path / "t2.transcript"
    tr_path2.write_text(
        textwrap.dedent(
            """\
            > echo hi
            bye
            """
        ),
        encoding="utf-8",
    )
    res2 = runner.run(tr_path2)
    assert not res2.passed
    assert res2.failures
    assert "echo hi" in res2.failures[0].command


def test_cmdloop_smoke():
    out = io.StringIO()
    err = io.StringIO()
    inp = io.StringIO("echo hi\nquit\n")
    app = App(stdin=inp, stdout=out, stderr=err)
    app.cmdloop(intro=None)
    assert "hi" in out.getvalue()