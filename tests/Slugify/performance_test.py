from __future__ import annotations

import os
import random
import string
import sys
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("SLUGIFY_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "python-slugify"
else:
    REPO_ROOT = ROOT / "generation" / "Slugify"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _install_unidecode_stub() -> None:
    """Install minimal stubs for unidecode / text_unidecode."""
    def _unidecode_func(s: str) -> str:
        return s

    uni_mod = types.ModuleType("unidecode")
    uni_mod.unidecode = _unidecode_func  # type: ignore[attr-defined]
    sys.modules["unidecode"] = uni_mod

    text_uni_mod = types.ModuleType("text_unidecode")
    text_uni_mod.unidecode = _unidecode_func  # type: ignore[attr-defined]
    sys.modules["text_unidecode"] = text_uni_mod


_install_unidecode_stub()

from slugify import slugify  # type: ignore  # noqa: E402


def _make_random_text(length: int) -> str:
    """Generate a pseudo-random mixed string."""
    letters = string.ascii_letters + string.digits + " -_./" + "影師嗎üéà"
    return "".join(random.choice(letters) for _ in range(length))


def _run_slugify_batch(batch_size: int = 500, text_length: int = 64) -> int:
    """Run slugify on a batch of strings and return total output length."""
    total_len = 0
    for _ in range(batch_size):
        text = _make_random_text(text_length)
        s = slugify(text)
        total_len += len(s)
    return total_len


def run_slugify_performance_benchmark(
    iterations: int = 10,
    batch_size: int = 500,
    text_length: int = 64,
) -> dict[str, float]:
    """Run repeated slugify batches and measure total time."""
    random.seed(42)
    total_out_len = 0

    t0 = time.perf_counter()
    for _ in range(iterations):
        total_out_len += _run_slugify_batch(batch_size=batch_size, text_length=text_length)
    t1 = time.perf_counter()

    total_time = t1 - t0
    total_calls = iterations * batch_size

    return {
        "iterations": float(iterations),
        "batch_size": float(batch_size),
        "text_length": float(text_length),
        "total_calls": float(total_calls),
        "total_time_seconds": float(total_time),
        "calls_per_second": float(total_calls / total_time) if total_time > 0 else 0.0,
        "total_output_length": float(total_out_len),
    }


def test_slugify_performance_smoke() -> None:
    """Smoke test to ensure the performance benchmark runs successfully."""
    metrics = run_slugify_performance_benchmark(iterations=3, batch_size=100, text_length=32)

    assert metrics["iterations"] == 3.0
    assert metrics["batch_size"] == 100.0
    assert metrics["text_length"] == 32.0
    assert metrics["total_calls"] == 300.0
    assert metrics["total_time_seconds"] >= 0.0
    assert metrics["calls_per_second"] >= 0.0
    assert metrics["total_output_length"] > 0.0
