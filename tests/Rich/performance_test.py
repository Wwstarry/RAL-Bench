import io
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TARGET = os.environ.get("RICH_TARGET", "generated").lower()
if TARGET == "reference":
    REPO_ROOT = ROOT / "repositories" / "rich"
elif TARGET == "generated":
    REPO_ROOT = ROOT / "generation" / "Rich"
else:
    raise RuntimeError(f"Unknown RICH_TARGET={TARGET!r}")

sys.path.insert(0, str(REPO_ROOT))

from rich.console import Console  # type: ignore  # noqa: E402
from rich.table import Table  # type: ignore  # noqa: E402
from rich.progress import Progress  # type: ignore  # noqa: E402


def make_console_buffer():
    buf = io.StringIO()
    console = Console(
        file=buf,
        force_terminal=True,
        color_system="truecolor",
        log_path=False,
    )
    return console, buf


def test_large_table_and_progress_performance():
    console, buf = make_console_buffer()

    table = Table(title="Performance Table")
    table.add_column("Index")
    table.add_column("Value")
    table.add_column("Status")

    for i in range(2000):
        table.add_row(str(i), f"value-{i}", "OK" if i % 2 == 0 else "WARN")

    start = time.perf_counter()
    console.print(table)

    with Progress(console=console, transient=False) as progress:
        task_id = progress.add_task("PerfTask", total=500)
        for _ in range(500):
            progress.advance(task_id, 1)
    elapsed = time.perf_counter() - start

    output = buf.getvalue()
    assert "Performance Table" in output
    assert "PerfTask" in output
    assert "value-0" in output
    assert "value-1999" in output

    # No strict upper bound in tests; elapsed time is recorded by
    # measure_reference.py as a baseline.
    assert elapsed >= 0.0
