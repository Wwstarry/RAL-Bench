from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pandas as pd  # type: ignore

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("LIFELINES_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "lifelines"
else:
    REPO_ROOT = ROOT / "generation" / "Lifelines"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lifelines import KaplanMeierFitter  # type: ignore  # noqa: E402


def _make_small_dataset(n: int = 100) -> pd.DataFrame:
    """Create a small synthetic dataset for repeated KMF fits."""
    durations = list(range(1, n + 1))
    events = [1 if i % 3 != 0 else 0 for i in durations]
    return pd.DataFrame({"duration": durations, "event": events})


def run_lifelines_performance_benchmark(iterations: int = 50, n: int = 100) -> dict[str, float]:
    """Run repeated KaplanMeierFitter fits and measure total time."""
    df = _make_small_dataset(n)
    kmf = KaplanMeierFitter()

    t0 = time.perf_counter()
    for _ in range(iterations):
        kmf.fit(df["duration"], df["event"])
    t1 = time.perf_counter()

    total_time = t1 - t0
    total_fits = iterations

    return {
        "iterations": float(iterations),
        "n_samples": float(n),
        "total_fits": float(total_fits),
        "total_time_seconds": float(total_time),
        "fits_per_second": float(total_fits / total_time) if total_time > 0 else 0.0,
    }


def test_lifelines_performance_smoke() -> None:
    """Smoke test to ensure the performance benchmark runs successfully."""
    metrics = run_lifelines_performance_benchmark(iterations=10, n=50)
    assert metrics["iterations"] == 10.0
    assert metrics["n_samples"] == 50.0
    assert metrics["total_fits"] == 10.0
    assert metrics["total_time_seconds"] >= 0.0
    assert metrics["fits_per_second"] >= 0.0
