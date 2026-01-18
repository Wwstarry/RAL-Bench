from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, List

import pytest

# -----------------------------------------------------------------------------
# RACB import contract:
# 1) Must use RACB_REPO_ROOT when provided (runner sets it).
# 2) Auto-detect two layouts:
#    - repo_root/<package>/__init__.py
#    - repo_root/src/<package>/__init__.py  -> sys.path inserts repo_root/src
# -----------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "typer"


def _select_repo_root() -> Path:
    override = os.environ.get("RACB_REPO_ROOT", "").strip()
    if override:
        return Path(override).resolve()

    target = os.environ.get("TYPER_TARGET", "reference").lower()
    if target == "reference":
        return (ROOT / "repositories" / "typer").resolve()
    return (ROOT / "generation" / "Typer").resolve()


REPO_ROOT = _select_repo_root()
if not REPO_ROOT.exists():
    pytest.skip(
        "RACB_REPO_ROOT does not exist on disk: {}".format(REPO_ROOT),
        allow_module_level=True,
    )

src_pkg_init = REPO_ROOT / "src" / PACKAGE / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE / "__init__.py"

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Could not find Typer package. Expected {} or {}.".format(src_pkg_init, root_pkg_init),
        allow_module_level=True,
    )

import typer  # type: ignore  # noqa: E402
from typer.testing import CliRunner  # type: ignore  # noqa: E402

runner = CliRunner()


# -----------------------------------------------------------------------------
# Apps used by tests
# -----------------------------------------------------------------------------

def _create_greeter_app() -> typer.Typer:
    """
    Single-command style app (callback-only):
      app NAME [--excited]
    """
    app = typer.Typer()

    @app.callback(invoke_without_command=True)
    def main(
        ctx: typer.Context,
        name: str = typer.Argument(...),
        excited: bool = typer.Option(False, "--excited"),
    ) -> None:
        if ctx.invoked_subcommand is not None:
            return
        msg = "Hello {}".format(name)
        if excited:
            msg += "!!!"
        typer.echo(msg)

    return app


def _create_todo_app() -> typer.Typer:
    """Small in-memory todo CLI with add/list/remove (multi-command)."""
    app = typer.Typer()
    todos: List[str] = []

    @app.command()
    def add(title: str) -> None:
        todos.append(title)
        typer.echo("Added: {}".format(title))

    @app.command()
    def list() -> None:  # type: ignore[override]
        if not todos:
            typer.echo("No tasks.")
            return
        for idx, item in enumerate(todos, start=1):
            typer.echo("{}. {}".format(idx, item))

    @app.command()
    def remove(index: int) -> None:
        removed = todos.pop(index - 1)
        typer.echo("Removed: {}".format(removed))

    return app


def _create_prompt_app() -> typer.Typer:
    """
    Multi-command app to avoid Typer's single-command "collapse" behavior in
    some versions. This guarantees that "greet" exists as a subcommand.
    """
    app = typer.Typer()

    @app.command()
    def greet(
        name: str = typer.Option(
            None,
            "--name",
            prompt=True,
            help="Name to greet (prompted when missing).",
        )
    ) -> None:
        typer.echo("Hi {}".format(name))

    @app.command()
    def noop() -> None:
        typer.echo("noop")

    return app


def _create_env_app() -> typer.Typer:
    """
    Multi-command app to guarantee that "show" exists as a subcommand.
    """
    app = typer.Typer()

    @app.command()
    def show(token: str = typer.Option(..., "--token", envvar="APP_TOKEN")) -> None:
        typer.echo("TOKEN={}".format(token))

    @app.command()
    def noop() -> None:
        typer.echo("noop")

    return app


def _create_callback_app() -> typer.Typer:
    """App with a callback global option that influences command output."""
    app = typer.Typer()
    state: Dict[str, bool] = {"verbose": False}

    @app.callback()
    def main(verbose: bool = typer.Option(False, "--verbose")) -> None:
        state["verbose"] = bool(verbose)

    @app.command()
    def run() -> None:
        if state["verbose"]:
            typer.echo("running (verbose)")
        else:
            typer.echo("running")

    return app


def _create_types_app() -> typer.Typer:
    """
    Multi-command app to guarantee that "calc" exists as a subcommand.
    Covers typed arguments and a float option.
    """
    app = typer.Typer()

    @app.command()
    def calc(x: int, y: int, scale: float = typer.Option(1.0, "--scale")) -> None:
        result = (x + y) * scale
        typer.echo("result={}".format(result))

    @app.command()
    def noop() -> None:
        typer.echo("noop")

    return app


# -----------------------------------------------------------------------------
# Tests (functional-only / happy path)
# -----------------------------------------------------------------------------

def test_simple_hello_command() -> None:
    app = _create_greeter_app()
    result = runner.invoke(app, ["World"])
    assert result.exit_code == 0
    assert "Hello World" in result.stdout


def test_simple_hello_command_excited() -> None:
    app = _create_greeter_app()
    # Safer ordering across Click versions: options before args.
    result = runner.invoke(app, ["--excited", "World"])
    assert result.exit_code == 0
    assert "Hello World!!!" in result.stdout


def test_greeter_help_mentions_option_and_argument() -> None:
    app = _create_greeter_app()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    out = result.stdout
    assert "--excited" in out
    assert "NAME" in out or "name" in out


def test_todo_list_empty_shows_no_tasks() -> None:
    app = _create_todo_app()
    r = runner.invoke(app, ["list"])
    assert r.exit_code == 0
    assert "No tasks." in r.stdout


def test_todo_add_and_list() -> None:
    app = _create_todo_app()

    r1 = runner.invoke(app, ["add", "Write tests"])
    r2 = runner.invoke(app, ["add", "Review PRs"])

    assert r1.exit_code == 0
    assert "Added: Write tests" in r1.stdout
    assert r2.exit_code == 0
    assert "Added: Review PRs" in r2.stdout

    r3 = runner.invoke(app, ["list"])
    assert r3.exit_code == 0
    out = r3.stdout
    assert "1. Write tests" in out
    assert "2. Review PRs" in out


def test_todo_remove_then_list_updates() -> None:
    app = _create_todo_app()

    runner.invoke(app, ["add", "Task 1"])
    runner.invoke(app, ["add", "Task 2"])

    r_remove = runner.invoke(app, ["remove", "1"])
    assert r_remove.exit_code == 0
    assert "Removed: Task 1" in r_remove.stdout

    r_list = runner.invoke(app, ["list"])
    assert r_list.exit_code == 0
    assert "1. Task 2" in r_list.stdout
    assert "Task 1" not in r_list.stdout


def test_help_output_includes_commands() -> None:
    app = _create_todo_app()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    out = result.stdout
    assert "add" in out
    assert "list" in out
    assert "remove" in out


def test_subcommand_help_for_add_mentions_argument() -> None:
    app = _create_todo_app()
    result = runner.invoke(app, ["add", "--help"])
    assert result.exit_code == 0
    out = result.stdout
    assert "TITLE" in out or "title" in out


def test_prompt_option_happy_path() -> None:
    app = _create_prompt_app()
    # Now stable: "greet" always exists as a subcommand (multi-command app).
    result = runner.invoke(app, ["greet"], input="Alice\n")
    assert result.exit_code == 0
    assert "Hi Alice" in result.stdout


def test_envvar_option_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    app = _create_env_app()
    monkeypatch.setenv("APP_TOKEN", "abc123")

    result = runner.invoke(app, ["show"])
    assert result.exit_code == 0
    assert "TOKEN=abc123" in result.stdout


def test_callback_global_option_affects_command_output() -> None:
    app = _create_callback_app()

    r1 = runner.invoke(app, ["run"])
    assert r1.exit_code == 0
    assert "running" in r1.stdout
    assert "verbose" not in r1.stdout

    r2 = runner.invoke(app, ["--verbose", "run"])
    assert r2.exit_code == 0
    assert "running (verbose)" in r2.stdout


def test_typed_arguments_and_float_option() -> None:
    app = _create_types_app()
    # Now stable: "calc" always exists as a subcommand (multi-command app).
    r = runner.invoke(app, ["calc", "2", "3", "--scale", "2.0"])
    assert r.exit_code == 0
    # (2+3)*2.0 = 10.0
    assert "result=10.0" in r.stdout
