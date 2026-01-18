import io
import os
import sys
from pathlib import Path

import psutil  # type: ignore

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


def _memory_mb() -> float:
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def test_memory_usage_for_repeated_rendering():
    console, buf = make_console_buffer()

    before = _memory_mb()

    for _ in range(5):
        table = Table(title="Resource Table")
        table.add_column("Index")
        table.add_column("Value")
        table.add_column("Flag")

        for i in range(3000):
            table.add_row(str(i), f"value-{i}", "X" if i % 3 == 0 else "O")

        console.print(table)

        with Progress(console=console, transient=False) as progress:
            task_id = progress.add_task("ResTask", total=200)
            for _ in range(200):
                progress.advance(task_id, 1)

    after = _memory_mb()

    output = buf.getvalue()
    assert "Resource Table" in output
    assert "ResTask" in output
    assert "value-0" in output
    assert "value-2999" in output

    delta = max(0.0, after - before)
    # Generous threshold to accommodate different platforms.
    assert delta < 300.0
