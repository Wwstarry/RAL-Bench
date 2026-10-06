import io
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TARGET = os.environ.get("LOGURU_TARGET", "generated").lower()
if TARGET == "reference":
    REPO_ROOT = ROOT / "repositories" / "loguru"
elif TARGET == "generated":
    REPO_ROOT = ROOT / "generation" / "Loguru"
else:
    raise RuntimeError(f"Unknown LOGURU_TARGET={TARGET!r}")

sys.path.insert(0, str(REPO_ROOT))

from loguru import logger  # type: ignore  # noqa: E402


def test_logging_throughput_for_many_messages():
    buf = io.StringIO()
    logger.remove()
    logger.add(buf, format="{level}:{message}", level="INFO")

    num_messages = 20000

    start = time.perf_counter()
    for i in range(num_messages):
        logger.info(f"msg-{i}")
    elapsed = time.perf_counter() - start

    output = buf.getvalue()
    # Sanity checks
    assert "msg-0" in output
    assert f"msg-{num_messages - 1}" in output

    # No explicit upper bound assertion; elapsed will be compared
    # against the reference implementation by the benchmark harness.
    assert elapsed >= 0.0
