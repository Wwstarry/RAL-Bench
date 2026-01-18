import os
import sys
from pathlib import Path

import psutil  # type: ignore
from PIL import Image  # type: ignore

#   <root>/tests/Stegano/resource_test.py
ROOT = Path(__file__).resolve().parents[2]

REPO_ROOT_ENV = "RACB_REPO_ROOT"


def _select_repo_root() -> Path:
    override = os.environ.get(REPO_ROOT_ENV)
    if override:
        return Path(override).resolve()

    target = os.environ.get("STEGANO_TARGET", "generated").lower()
    if target == "reference":
        return (ROOT / "repositories" / "Stegano").resolve()
    return (ROOT / "generation" / "Stegano").resolve()


REPO_ROOT = _select_repo_root()
if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from stegano import lsb  # type: ignore

REFERENCE_ROOT = ROOT / "repositories" / "Stegano"
SAMPLE_FILES = REFERENCE_ROOT / "tests" / "sample-files"
LENNA_PNG = SAMPLE_FILES / "Lenna.png"


def test_resource_usage_smoke() -> None:
    """
    Smoke test: exercise a representative workload.

    Important:
      - Benchmark runner (measure_generated.py) measures resource usage of pytest subprocess.
      - This test remains a correctness-oriented smoke test.
    """
    assert LENNA_PNG.exists(), f"Missing sample file: {LENNA_PNG}"

    proc = psutil.Process()
    rss_before = proc.memory_info().rss

    secret = "resource secret"
    out = REPO_ROOT / "tmp_resource.png"

    encoded_img = lsb.hide(str(LENNA_PNG), secret)  # returns PIL.Image
    encoded_img.save(str(out))
    assert out.exists()

    with Image.open(out) as img:
        img.load()

    rss_after = proc.memory_info().rss
    rss_delta_mb = (rss_after - rss_before) / (1024 * 1024)
    print(f"RSS delta (MB): {rss_delta_mb:.2f}")

    assert rss_after > 0
