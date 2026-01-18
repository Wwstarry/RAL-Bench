import os
import sys
import time
import statistics
from pathlib import Path

#   <root>/tests/Stegano/performance_test.py
ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("STEGANO_TARGET", "generated").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "Stegano"
else:
    REPO_ROOT = ROOT / "generation" / "Stegano"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from stegano import lsb  # type: ignore
from PIL import Image  # type: ignore

REFERENCE_ROOT = ROOT / "repositories" / "Stegano"
SAMPLE_FILES = REFERENCE_ROOT / "tests" / "sample-files"
LENNA_PNG = SAMPLE_FILES / "Lenna.png"


def _ensure_sample_files_exist() -> None:
    assert LENNA_PNG.exists(), f"Missing sample file: {LENNA_PNG}"


def _measure_hide_reveal(iterations: int = 10):
    _ensure_sample_files_exist()

    tmp_dir = ROOT / "tmp_perf"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    output_img = tmp_dir / "Lenna-lsb-perf.png"

    hide_times = []
    reveal_times = []

    message = "Performance benchmark message for Stegano" * 3

    for _ in range(iterations):
        start = time.perf_counter()
        secret_img = lsb.hide(str(LENNA_PNG), message)
        secret_img.save(output_img)
        hide_times.append(time.perf_counter() - start)

        start = time.perf_counter()
        _ = lsb.reveal(str(output_img))
        reveal_times.append(time.perf_counter() - start)

    return statistics.mean(hide_times), statistics.mean(reveal_times)


def test_lsb_performance_smoke() -> None:
    """Simple performance sanity check for LSB hide/reveal."""
    avg_hide, avg_reveal = _measure_hide_reveal(iterations=5)
    print(f"Average hide time: {avg_hide:.6f}s, reveal time: {avg_reveal:.6f}s")
    assert avg_hide > 0.0
    assert avg_reveal > 0.0
