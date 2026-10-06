from __future__ import annotations

import os
import sys
import time
from pathlib import Path
import textwrap

# Root directory of the benchmark project
ROOT = Path(__file__).resolve().parents[2]

# Decide whether to test the reference repository or the generated one.
target = os.environ.get("MARKDOWN_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "markdown"
else:
    # This should be the path where generated Markdown repositories are stored.
    REPO_ROOT = ROOT / "generation" / "Markdown"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import markdown  # type: ignore  # noqa: E402


def _build_corpus() -> list[str]:
    """Build a small synthetic corpus of Markdown documents for performance tests.

    The corpus mixes headings, lists, code blocks, blockquotes and links in order
    to exercise a representative subset of the Markdown implementation.
    """
    base_doc = textwrap.dedent(
        """
        # Document {i}

        This is a sample paragraph with some *emphasis*, **strong emphasis**,
        and `inline_code()` sprinkled throughout. It also contains a [link](https://example.com)
        and an image: ![alt text](https://example.com/image.png).

        ## Lists

        - item 1
        - item 2
        - item 3

        1. first
        2. second
        3. third

        ## Code

        ```python
        def foo(x: int) -> int:
            return x * x
        ```

        > A blockquote that mentions <b>HTML</b> tags in passing.

        ---
        """
    ).strip("\n")

    docs: list[str] = []
    # Create multiple documents by formatting the base template.
    for i in range(20):
        docs.append(base_doc.format(i=i))
    return docs


def run_markdown_performance_benchmark() -> dict[str, float]:
    """Run a simple performance benchmark over a synthetic Markdown corpus.

    Returns a dictionary with total time, total characters processed and
    derived throughput (characters per second). This function is intended
    to be reused by the benchmark harness to compute non-functional scores.
    """
    docs = _build_corpus()
    total_chars = sum(len(doc) for doc in docs)

    t0 = time.perf_counter()
    for doc in docs:
        _ = markdown.markdown(doc)
    t1 = time.perf_counter()

    total_time = t1 - t0
    throughput = total_chars / total_time if total_time > 0 else 0.0

    return {
        "num_documents": float(len(docs)),
        "total_chars": float(total_chars),
        "total_time_seconds": float(total_time),
        "throughput_chars_per_second": float(throughput),
    }


def test_markdown_performance_smoke() -> None:
    """Smoke test to ensure the performance benchmark can run without errors.

    The actual non-functional comparison between reference and generated
    repositories should be done by the external benchmark harness using
    the metrics returned by run_markdown_performance_benchmark().
    """
    metrics = run_markdown_performance_benchmark()
    # Basic sanity checks: values should be non-negative and time > 0.
    assert metrics["num_documents"] > 0
    assert metrics["total_chars"] > 0
    assert metrics["total_time_seconds"] > 0.0
    assert metrics["throughput_chars_per_second"] > 0.0
