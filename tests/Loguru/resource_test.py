import io
import os
import sys
from pathlib import Path

import psutil  # type: ignore

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


def _memory_mb() -> float:
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def test_memory_usage_for_repeated_logging():
    buf = io.StringIO()
    logger.remove()
    logger.add(buf, format="{level}:{message}", level="INFO")

    before = _memory_mb()

    for _ in range(5):
        for i in range(5000):
            logger.info(f"resource-msg-{i}")

    after = _memory_mb()
    output = buf.getvalue()

    # Sanity check: some messages should be present
    assert "resource-msg-0" in output
    assert "resource-msg-4999" in output

    delta = max(0.0, after - before)
    # Generous upper bound to allow for different platforms and Python builds.
    assert delta < 300.0
