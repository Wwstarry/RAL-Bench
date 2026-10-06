from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("PYGMENTS_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "pygments"
else:
    REPO_ROOT = ROOT / "generation" / "Pygments"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pygments  # type: ignore  # noqa: E402
from pygments.lexers import PythonLexer  # type: ignore  # noqa: E402
from pygments.formatters import HtmlFormatter  # type: ignore  # noqa: E402


def _build_sample_source(lines: int = 200) -> str:
    """Build a synthetic Python source file with a given number of lines."""
    base = "def func_{i}(x):\n    for j in range(10):\n        x += j\n    return x\n"
    return "\n".join(base.format(i=i) for i in range(lines))


def run_pygments_performance_benchmark(iterations: int = 50, lines: int = 200) -> dict[str, float]:
    """Run repeated highlighting on synthetic Python source and measure time."""
    code = _build_sample_source(lines=lines)
    lexer = PythonLexer()
    formatter = HtmlFormatter()

    t0 = time.perf_counter()
    total_chars = 0
    for _ in range(iterations):
        html = pygments.highlight(code, lexer, formatter)
        total_chars += len(html)
    t1 = time.perf_counter()

    total_time = t1 - t0
    return {
        "iterations": float(iterations),
        "lines": float(lines),
        "total_time_seconds": float(total_time),
        "avg_time_per_iteration": float(total_time / iterations) if iterations > 0 else 0.0,
        "output_chars": float(total_chars),
        "output_chars_per_second": float(total_chars / total_time) if total_time > 0 else 0.0,
    }


def test_pygments_performance_smoke() -> None:
    """Smoke test to ensure the performance benchmark runs successfully."""
    metrics = run_pygments_performance_benchmark(iterations=10, lines=100)

    assert metrics["iterations"] == 10.0
    assert metrics["lines"] == 100.0
    assert metrics["total_time_seconds"] >= 0.0
    assert metrics["avg_time_per_iteration"] >= 0.0
    assert metrics["output_chars"] > 0.0
    assert metrics["output_chars_per_second"] >= 0.0
