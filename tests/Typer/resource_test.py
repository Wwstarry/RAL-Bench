from __future__ import annotations

import os
import sys
from pathlib import Path

# Root directory of the benchmark project
ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("TYPER_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "typer"
else:
    REPO_ROOT = ROOT / "generation" / "Typer"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import typer  # type: ignore  # noqa: E402
from typer.testing import CliRunner  # type: ignore  # noqa: E402


runner = CliRunner()


def _create_project_app() -> typer.Typer:
    """Create a multi-command project management CLI for integration testing."""
    app = typer.Typer()
    tasks: dict[str, list[str]] = {}

    @app.command()
    def init(name: str) -> None:
        if name in tasks:
            typer.echo(f"Project {name} already exists.")
            raise typer.Exit(code=1)
        tasks[name] = []
        typer.echo(f"Initialized project {name}")

    @app.command()
    def add_task(project: str, title: str) -> None:
        if project not in tasks:
            typer.echo(f"Unknown project: {project}")
            raise typer.Exit(code=1)
        tasks[project].append(title)
        typer.echo(f"Added task to {project}: {title}")

    @app.command()
    def list_tasks(project: str) -> None:
        if project not in tasks:
            typer.echo(f"Unknown project: {project}")
            raise typer.Exit(code=1)
        if not tasks[project]:
            typer.echo(f"No tasks for project {project}")
            return
        for idx, title in enumerate(tasks[project], start=1):
            typer.echo(f"{idx}. {title}")

    return app


def test_project_workflow_integration() -> None:
    """End-to-end test of initializing a project and managing tasks."""
    app = _create_project_app()

    r1 = runner.invoke(app, ["init", "demo"])
    assert r1.exit_code == 0
    assert "Initialized project demo" in r1.stdout

    # Command names follow Click/Typer convention: underscores in function
    # names become hyphens in the CLI, so we must use "add-task" here.
    r2 = runner.invoke(app, ["add-task", "demo", "Write docs"])
    r3 = runner.invoke(app, ["add-task", "demo", "Implement feature"])

    assert r2.exit_code == 0
    assert r3.exit_code == 0

    r4 = runner.invoke(app, ["list-tasks", "demo"])
    out = r4.stdout
    assert "1. Write docs" in out
    assert "2. Implement feature" in out


def test_help_output_for_integration_app() -> None:
    app = _create_project_app()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    out = result.stdout
    # Help output should contain command names and descriptions.
    assert "init" in out
    assert "add-task" in out or "add_task" in out
    assert "list-tasks" in out or "list_tasks" in out
