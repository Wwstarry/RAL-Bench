# tests/Celery/resource_test.py
from __future__ import annotations

import gc
import sys
import tracemalloc
from pathlib import Path
from typing import List

import pytest


def _ensure_celery_importable() -> None:
    try:
        import celery  # noqa: F401
        return
    except Exception:
        pass

    root = Path(__file__).resolve().parents[2]
    ref_repo = root / "repositories" / "celery"
    if ref_repo.exists():
        sys.path.insert(0, str(ref_repo))

    import celery  # noqa: F401


def _make_app(name: str = "celery_resource_app"):
    _ensure_celery_importable()
    from celery import Celery

    app = Celery(name, broker="memory://", backend="cache+memory://")
    app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        task_store_eager_result=False,  # reduce retained objects
        broker_url="memory://",
        result_backend="cache+memory://",
        enable_utc=True,
        timezone="UTC",
        accept_content=["json"],
        task_serializer="json",
        result_serializer="json",
    )
    return app


@pytest.mark.resource
def test_resource_001_tracemalloc_growth_is_bounded_for_many_tasks() -> None:
    """
    Use tracemalloc (stdlib) so the test stays portable.
    We only check that memory growth is not pathological.
    """
    app = _make_app()

    @app.task(name="celery_resource.small")
    def small(x: int) -> int:
        return x + 1

    gc.collect()
    tracemalloc.start()
    snap0 = tracemalloc.take_snapshot()

    n = 8000
    for i in range(n):
        r = small.delay(i)
        _ = r.get(timeout=2)

    gc.collect()
    snap1 = tracemalloc.take_snapshot()
    stats = snap1.compare_to(snap0, "lineno")

    # Sum of positive diffs (bytes). Conservative limit.
    pos = 0
    for st in stats:
        if st.size_diff > 0:
            pos += st.size_diff

    tracemalloc.stop()

    # 80 MB is generous for Python object churn; adjust later if needed.
    assert pos < 80 * 1024 * 1024, f"excessive tracemalloc growth: {pos / (1024 * 1024):.2f} MB"


@pytest.mark.resource
def test_resource_002_repeated_app_creation_does_not_leak_excessively() -> None:
    gc.collect()
    tracemalloc.start()
    snap0 = tracemalloc.take_snapshot()

    apps = []
    for i in range(30):
        apps.append(_make_app(f"celery_resource_app_{i}"))

    # drop references
    apps.clear()
    gc.collect()

    snap1 = tracemalloc.take_snapshot()
    stats = snap1.compare_to(snap0, "lineno")

    pos = 0
    for st in stats:
        if st.size_diff > 0:
            pos += st.size_diff

    tracemalloc.stop()

    assert pos < 50 * 1024 * 1024, f"excessive growth after app churn: {pos / (1024 * 1024):.2f} MB"
