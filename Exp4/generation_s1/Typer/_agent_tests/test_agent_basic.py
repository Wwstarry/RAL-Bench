import pytest
import typer
from typer.testing import CliRunner


def test_basic_command_and_echo():
    app = typer.Typer()

    @app.command()
    def hello(name: str):
        typer.echo(f"Hello {name}")

    r = CliRunner().invoke(app, ["hello", "World"])
    assert r.exit_code == 0
    assert r.stdout.strip() == "Hello World"
    assert r.stderr == ""


def test_options_long_short_and_default_and_equals():
    app = typer.Typer()

    @app.command()
    def cmd(
        name: str = typer.Option("x", "--name", "-n", help="Name"),
        age: int = typer.Option(10, "--age"),
    ):
        typer.echo(f"{name}:{age}")

    runner = CliRunner()
    r1 = runner.invoke(app, ["cmd"])
    assert r1.exit_code == 0
    assert r1.stdout.strip() == "x:10"

    r2 = runner.invoke(app, ["cmd", "--name", "bob", "--age=3"])
    assert r2.exit_code == 0
    assert r2.stdout.strip() == "bob:3"

    r3 = runner.invoke(app, ["cmd", "-n", "ann"])
    assert r3.exit_code == 0
    assert r3.stdout.strip() == "ann:10"


def test_required_option_and_argument_errors_exit_2_to_stderr():
    app = typer.Typer()

    @app.command()
    def cmd(
        x: int = typer.Option(..., "--x"),
        name: str = typer.Argument(...),
    ):
        typer.echo(f"{x}-{name}")

    runner = CliRunner()
    r1 = runner.invoke(app, ["cmd", "bob"])
    assert r1.exit_code == 2
    assert "Missing option" in r1.stderr

    r2 = runner.invoke(app, ["cmd", "--x", "1"])
    assert r2.exit_code == 2
    assert "Missing argument" in r2.stderr


def test_bool_flag_and_no_flag():
    app = typer.Typer()

    @app.command()
    def cmd(flag: bool = typer.Option(False, "--flag")):
        typer.echo("yes" if flag else "no")

    runner = CliRunner()
    r1 = runner.invoke(app, ["cmd"])
    assert r1.stdout.strip() == "no"
    r2 = runner.invoke(app, ["cmd", "--flag"])
    assert r2.stdout.strip() == "yes"

    app2 = typer.Typer()

    @app2.command()
    def cmd2(flag: bool = typer.Option(True, "--flag")):
        typer.echo("yes" if flag else "no")

    r3 = runner.invoke(app2, ["cmd2", "--no-flag"])
    assert r3.exit_code == 0
    assert r3.stdout.strip() == "no"


def test_help_includes_usage_commands_and_show_message():
    app = typer.Typer(help="App help text")

    @app.command(help="Do foo")
    def foo():
        pass

    @app.command()
    def bar():
        """Do bar."""
        pass

    runner = CliRunner()
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    assert "Usage:" in r.stdout
    assert "Commands:" in r.stdout
    assert "foo" in r.stdout
    assert "bar" in r.stdout
    assert "Show this message and exit." in r.stdout

    r2 = runner.invoke(app, ["foo", "--help"])
    assert r2.exit_code == 0
    assert "Usage:" in r2.stdout
    assert "Options:" in r2.stdout


def test_exit_propagation_exit_and_return_int():
    app = typer.Typer()

    @app.command()
    def a():
        raise typer.Exit(code=3)

    @app.command()
    def b():
        return 5

    runner = CliRunner()
    r1 = runner.invoke(app, ["a"])
    assert r1.exit_code == 3
    r2 = runner.invoke(app, ["b"])
    assert r2.exit_code == 5


def test_unknown_command_exit_2_and_shows_help():
    app = typer.Typer()

    @app.command()
    def ok():
        pass

    r = CliRunner().invoke(app, ["nope"])
    assert r.exit_code == 2
    assert "No such command" in r.stderr
    assert "Commands:" in r.stdout


def test_stderr_capture_echo_err_true():
    app = typer.Typer()

    @app.command()
    def cmd():
        typer.echo("out")
        typer.echo("err", err=True)

    r = CliRunner().invoke(app, ["cmd"])
    assert r.exit_code == 0
    assert r.stdout.strip() == "out"
    assert r.stderr.strip() == "err"
    assert r.output.strip().endswith("err")


def test_catch_exceptions_behavior():
    app = typer.Typer()

    @app.command()
    def boom():
        raise RuntimeError("nope")

    runner = CliRunner()
    r = runner.invoke(app, ["boom"], catch_exceptions=True)
    assert r.exit_code == 1
    assert isinstance(r.exception, RuntimeError)

    with pytest.raises(RuntimeError):
        runner.invoke(app, ["boom"], catch_exceptions=False)