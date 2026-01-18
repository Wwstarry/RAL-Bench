import os
import sys
from pathlib import Path

import psutil  # type: ignore

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


def _memory_mb() -> float:
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def test_repeated_invocations_memory_usage():
    @click.command()
    @click.option("--times", type=int, default=1)
    @click.argument("name")
    def greet(times: int, name: str) -> None:
        for _ in range(times):
            click.echo(f"Hello {name}!")

    runner = CliRunner()

    before = _memory_mb()

    for i in range(300):
        result = runner.invoke(greet, ["--times", "3", f"User-{i}"])
        assert result.exit_code == 0

    after = _memory_mb()
    delta = max(0.0, after - before)

    # Very generous limit to just catch runaway leaks.
    assert delta < 300.0
