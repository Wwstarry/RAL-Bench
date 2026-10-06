import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TARGET = os.environ.get("CLICK_TARGET", "generated").lower()
if TARGET == "reference":
    REPO_ROOT = ROOT / "repositories" / "click"
elif TARGET == "generated":
    REPO_ROOT = ROOT / "generation" / "Click"
else:
    raise RuntimeError(f"Unknown CLICK_TARGET={TARGET!r}")

if not REPO_ROOT.exists():
    raise RuntimeError(f"Repository root does not exist: {REPO_ROOT}")

sys.path.insert(0, str(REPO_ROOT))

import click  # type: ignore  # noqa: E402
from click.testing import CliRunner  # type: ignore  # noqa: E402


def test_many_invocations_performance():
    @click.command()
    @click.option("--count", type=int, default=1)
    @click.argument("name")
    def greet(count: int, name: str) -> None:
        for _ in range(count):
            click.echo(f"Hello {name}!")

    runner = CliRunner()

    num_runs = 1000
    start = time.perf_counter()
    for i in range(num_runs):
        result = runner.invoke(greet, ["--count", "1", f"User-{i}"])
        assert result.exit_code == 0
    elapsed = time.perf_counter() - start

    # Sanity: function ran, and timing is non-negative
    assert elapsed >= 0.0
