from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

import pytest

ROOT = Path(__file__).resolve().parents[2]

# Decide whether to test the reference repo or a generated repo.
target = os.environ.get("XMLTODICT_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "xmltodict"
else:
    REPO_ROOT = ROOT / "generation" / "Xmltodict"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import xmltodict  # type: ignore  # noqa: E402


_LARGE_XML_TEMPLATE = """
<root>
  <users>
    {users}
  </users>
</root>
""".strip()


def _make_large_xml(n: int = 200) -> str:
    """Generate a synthetic XML document with n user elements."""
    user_tpl = '<user id="{id}"><name>User{id}</name><age>{age}</age></user>'
    users_xml = "\n    ".join(
        user_tpl.format(id=i, age=20 + (i % 30)) for i in range(n)
    )
    return _LARGE_XML_TEMPLATE.format(users=users_xml)


def run_xmltodict_performance_benchmark(
    iterations: int = 20,
    n_users: int = 200,
) -> Dict[str, Any]:
    """
    Parse and unparse a moderately large XML document multiple times and
    measure total runtime.

    The returned metrics are used by the benchmark harness to compare the
    generated implementation against the reference implementation.
    """
    xml = _make_large_xml(n_users)

    start = time.perf_counter()
    parsed: Dict[str, Any] = {}
    for _ in range(iterations):
        parsed = xmltodict.parse(xml)
    mid = time.perf_counter()
    for _ in range(iterations):
        _ = xmltodict.unparse(parsed)
    end = time.perf_counter()

    parse_time = mid - start
    unparse_time = end - mid
    total_time = end - start

    return {
        "iterations": float(iterations),
        "n_users": float(n_users),
        "parse_time_s": float(parse_time),
        "unparse_time_s": float(unparse_time),
        "total_time_s": float(total_time),
    }


def test_xmltodict_performance_smoke() -> None:
    """Smoke test to ensure the performance benchmark runs successfully."""
    metrics = run_xmltodict_performance_benchmark(iterations=5, n_users=50)

    assert metrics["iterations"] == 5.0
    assert metrics["n_users"] == 50.0
    assert metrics["parse_time_s"] >= 0.0
    assert metrics["unparse_time_s"] >= 0.0
    assert metrics["total_time_s"] >= 0.0
