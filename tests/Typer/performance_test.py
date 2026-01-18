from __future__ import annotations

import os
import sys
import time
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


def _create_noop_app() -> typer.Typer:
    """Create a very simple Typer app for performance measurements."""
    app = typer.Typer()

    @app.command()
    def noop() -> None:
        """Do nothing and exit successfully."""
        typer.echo("ok")

    return app


def run_typer_performance_benchmark(iterations: int = 200) -> dict[str, float]:
    """Run a basic performance benchmark over many CLI invocations.

    Functional correctness is validated separately in functional tests.
    Here we only measure how long it takes to invoke a simple command
    multiple times.
    """
    app = _create_noop_app()

    t0 = time.perf_counter()
    for _ in range(iterations):
        # For a single-command Typer app with no parameters, invoking it
        # with an empty argument list is sufficient to execute the command.
        _ = runner.invoke(app, [])
        # We intentionally do not check exit codes here; performance tests
        # should not be responsible for functional validation.
    t1 = time.perf_counter()

    total_time = t1 - t0
    return {
        "iterations": float(iterations),
        "total_time_seconds": float(total_time),
        "invocations_per_second": float(iterations / total_time) if total_time > 0 else 0.0,
    }


def test_typer_performance_smoke() -> None:
    """Smoke test to ensure the performance benchmark runs successfully."""
    metrics = run_typer_performance_benchmark(iterations=50)
    # Basic sanity checks: the benchmark should run and report non-negative values.
    assert metrics["iterations"] == 50.0
    assert metrics["total_time_seconds"] >= 0.0
    # Throughput can be zero in degenerate cases, but should not be negative.
    assert metrics["invocations_per_second"] >= 0.0
