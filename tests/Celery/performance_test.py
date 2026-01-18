# tests/Celery/performance_test.py
from __future__ import annotations

import sys
import time
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


def _make_app(name: str = "celery_perf_app"):
    _ensure_celery_importable()
    from celery import Celery

    app = Celery(name, broker="memory://", backend="cache+memory://")
    app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        task_store_eager_result=False,  # reduce overhead
        broker_url="memory://",
        result_backend="cache+memory://",
        enable_utc=True,
        timezone="UTC",
        accept_content=["json"],
        task_serializer="json",
        result_serializer="json",
    )
    return app


@pytest.mark.performance
def test_performance_001_many_small_tasks_finish_quickly() -> None:
    """
    Absolute threshold is intentionally conservative to avoid false failures on slow CI.
    """
    app = _make_app()

    @app.task(name="celery_perf.noop")
    def noop(x: int) -> int:
        return x

    n = 5000
    t0 = time.perf_counter()
    for i in range(n):
        r = noop.delay(i)
        _ = r.get(timeout=2)
    dt = time.perf_counter() - t0

    # Very conservative ceiling; baseline will be measured in your harness anyway.
    assert dt < 12.0, f"too slow for {n} eager tasks: {dt:.3f}s"


@pytest.mark.performance
def test_performance_002_group_batching_is_reasonable() -> None:
    app = _make_app()
    from celery import group

    @app.task(name="celery_perf.inc")
    def inc(x: int) -> int:
        return x + 1

    n = 2000
    t0 = time.perf_counter()
    r = group(inc.s(i) for i in range(n)).apply_async()
    out = r.get(timeout=10)
    dt = time.perf_counter() - t0

    assert len(out) == n
    assert out[0] == 1 and out[-1] == n
    assert dt < 12.0, f"too slow for group({n}): {dt:.3f}s"
