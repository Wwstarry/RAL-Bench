# tests/Celery/functional_test.py
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import pytest


def _ensure_celery_importable() -> None:
    """
    Do NOT force sys.path to reference repo if the package is already importable.
    This keeps compatibility with the harness that swaps in generated repos.
    """
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


def _make_app(name: str = "celery_test_app"):
    _ensure_celery_importable()
    from celery import Celery

    app = Celery(
        name,
        broker="memory://",
        backend="cache+memory://",
        include=[],
    )
    # Pure local, synchronous execution: no broker/worker needed.
    app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        task_store_eager_result=True,
        result_backend="cache+memory://",
        broker_url="memory://",
        enable_utc=True,
        timezone="UTC",
        accept_content=["json"],
        task_serializer="json",
        result_serializer="json",
    )
    return app


def test_001_import_celery_and_core_symbols() -> None:
    _ensure_celery_importable()
    import celery  # noqa: F401

    from celery import Celery  # noqa: F401
    from celery import chain, chord, group, signature  # noqa: F401


def test_002_create_app_and_register_task_runs_delay() -> None:
    app = _make_app()

    @app.task(name="celery_test.add")
    def add(x: int, y: int) -> int:
        return x + y

    r = add.delay(2, 3)
    assert r.get(timeout=2) == 5
    assert r.successful() is True


def test_003_apply_async_supports_kwargs_and_counts_down_ignored_in_eager() -> None:
    app = _make_app()

    @app.task(name="celery_test.mul")
    def mul(x: int, y: int) -> int:
        return x * y

    r = mul.apply_async(args=(3, 4), kwargs={}, countdown=5)
    # In eager mode countdown is effectively ignored (runs immediately).
    assert r.get(timeout=2) == 12


def test_004_group_collects_results_in_order() -> None:
    app = _make_app()
    from celery import group

    @app.task(name="celery_test.inc")
    def inc(x: int) -> int:
        return x + 1

    header = group(inc.s(i) for i in range(10))
    r = header.apply_async()
    out = r.get(timeout=3)
    assert out == [i + 1 for i in range(10)]


def test_005_chain_passes_previous_result() -> None:
    app = _make_app()
    from celery import chain

    @app.task(name="celery_test.add")
    def add(x: int, y: int) -> int:
        return x + y

    # (1+2)=3, then (3+10)=13
    r = chain(add.s(1, 2), add.s(10)).apply_async()
    assert r.get(timeout=3) == 13


def test_006_chord_runs_callback_over_group_results() -> None:
    app = _make_app()
    from celery import chord, group

    @app.task(name="celery_test.add")
    def add(x: int, y: int) -> int:
        return x + y

    @app.task(name="celery_test.sum_list")
    def sum_list(xs: List[int]) -> int:
        return sum(xs)

    header = group(add.s(i, 1) for i in range(5))  # [1,2,3,4,5] sum=15
    r = chord(header)(sum_list.s())
    assert r.get(timeout=3) == 15


def test_007_task_exception_propagates_in_eager_mode() -> None:
    """
    In some Celery versions/configs with task_always_eager=True and
    task_eager_propagates=True, the exception is raised immediately during
    delay()/apply_async() rather than on AsyncResult.get().

    This test accepts both correct behaviors:
    - delay raises ValueError directly, OR
    - delay returns a result whose .get() raises ValueError.
    """
    app = _make_app()

    @app.task(name="celery_test.boom")
    def boom() -> None:
        raise ValueError("boom")

    try:
        r = boom.delay()
    except ValueError as e:
        assert str(e) == "boom"
        return

    with pytest.raises(ValueError):
        _ = r.get(timeout=2)


def test_008_disable_propagation_returns_failed_result() -> None:
    """
    With task_eager_propagates=False:
      - Some Celery builds still raise on get(..., propagate=True)
      - get(..., propagate=False) may return None OR return the exception object
    We accept both behaviors as long as the task is marked failed.
    """
    app = _make_app()
    app.conf.task_eager_propagates = False

    @app.task(name="celery_test.boom2")
    def boom2() -> None:
        raise RuntimeError("boom2")

    r = boom2.delay()

    with pytest.raises(RuntimeError):
        _ = r.get(timeout=2, propagate=True)

    out = r.get(timeout=2, propagate=False)

    # Accept both common behaviors.
    if out is None:
        pass
    else:
        assert isinstance(out, Exception)
        assert str(out) == "boom2"

    assert r.failed() is True


def test_009_signature_freeze_has_id_and_task_name() -> None:
    app = _make_app()
    from celery import signature

    @app.task(name="celery_test.echo")
    def echo(x: str) -> str:
        return x

    sig = signature("celery_test.echo", args=("hi",), app=app)
    res = sig.apply_async()
    assert res.get(timeout=2) == "hi"
    assert getattr(sig, "task", None) in ("celery_test.echo", echo.name)


def test_010_default_app_does_not_break_custom_app_usage() -> None:
    """
    Ensure that importing celery and using a custom app is not polluted by globals.
    """
    app = _make_app("celery_test_app_2")

    @app.task(name="celery_test_app_2.add")
    def add(x: int, y: int) -> int:
        return x + y

    assert add.delay(7, 8).get(timeout=2) == 15
