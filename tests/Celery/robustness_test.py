# tests/Celery/robustness_test.py
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def _make_app(name: str = "celery_robust_app"):
    _ensure_celery_importable()
    from celery import Celery

    app = Celery(name, broker="memory://", backend="cache+memory://")
    app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        task_store_eager_result=True,
        broker_url="memory://",
        result_backend="cache+memory://",
        enable_utc=True,
        timezone="UTC",
        accept_content=["json"],
        task_serializer="json",
        result_serializer="json",
    )
    return app


def test_001_empty_args_and_kwargs_do_not_crash() -> None:
    app = _make_app()

    @app.task(name="celery_robust.const")
    def const() -> int:
        return 42

    r = const.apply_async(args=(), kwargs={})
    assert r.get(timeout=2) == 42


def test_002_unknown_task_name_signature_errors_cleanly() -> None:
    app = _make_app()
    from celery import signature

    sig = signature("celery_robust.nonexistent_task", args=(1,), app=app)
    with pytest.raises(Exception):
        _ = sig.apply_async().get(timeout=2)


def test_003_large_payload_does_not_crash_eager_execution() -> None:
    app = _make_app()

    @app.task(name="celery_robust.echo_len")
    def echo_len(s: str) -> int:
        return len(s)

    big = "x" * 2_000_000  # 2MB string
    r = echo_len.delay(big)
    assert r.get(timeout=5) == len(big)


def test_004_chord_with_empty_header_behaves_reasonably() -> None:
    app = _make_app()
    from celery import chord, group

    @app.task(name="celery_robust.cb")
    def cb(xs: List[int]) -> int:
        return sum(xs)

    header = group([])  # empty
    r = chord(header)(cb.s())
    assert r.get(timeout=2) == 0


def test_005_task_can_return_dict_and_list() -> None:
    app = _make_app()

    @app.task(name="celery_robust.make_obj")
    def make_obj() -> Dict[str, Any]:
        return {"a": 1, "b": [1, 2, 3], "c": {"x": "y"}}

    r = make_obj.delay()
    out = r.get(timeout=2)
    assert out["a"] == 1
    assert out["b"] == [1, 2, 3]
    assert out["c"]["x"] == "y"


def test_006_propagation_toggle_is_respected() -> None:
    app = _make_app()

    @app.task(name="celery_robust.fail")
    def fail() -> None:
        raise ValueError("bad")

    # propagate=True (default with task_eager_propagates=True)
    with pytest.raises(ValueError):
        _ = fail.delay().get(timeout=2)

    # now disable propagation
    app.conf.task_eager_propagates = False
    r = fail.delay()
    assert r.failed() is True
    # propagate=False should not raise here
    _ = r.get(timeout=2, propagate=False)
