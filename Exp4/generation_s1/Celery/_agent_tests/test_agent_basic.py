import time
import pytest

import celery
from celery import Celery
from celery.exceptions import TimeoutError


def test_imports():
    assert hasattr(celery, "Celery")
    assert Celery is celery.Celery


def test_task_decorator_and_registry_default_name():
    app = Celery("t1", broker_url="memory://", result_backend="memory://")

    @app.task
    def add(x, y):
        return x + y

    assert add.name in app.tasks
    r = add.delay(2, 3)
    assert r.get(timeout=2) == 5
    assert r.successful()


def test_task_decorator_custom_name_and_send_task():
    app = Celery("t2", broker="memory://", backend="memory://")

    @app.task(name="custom.mul")
    def mul(x, y):
        return x * y

    r = app.send_task("custom.mul", args=(6, 7))
    assert r.get(timeout=2) == 42


def test_bind_true_sets_request_and_app():
    app = Celery("t3", broker_url="memory://", result_backend="memory://")

    @app.task(bind=True, name="custom.bound")
    def bound(self, x):
        assert self.app is app
        assert self.request is not None
        assert self.request.id
        return (self.request.id, x)

    res = bound.delay(10)
    tid, val = res.get(timeout=2)
    assert val == 10
    assert tid == res.id


def test_eager_execution_success_and_store_result_default_true():
    app = Celery("t4", broker_url="memory://", result_backend="memory://")
    app.conf.task_always_eager = True

    @app.task
    def inc(x):
        return x + 1

    r = inc.delay(1)
    assert r.successful()
    assert r.get(timeout=0.1) == 2


def test_eager_propagates_exception_when_enabled():
    app = Celery("t5", broker_url="memory://", result_backend="memory://")
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True

    @app.task
    def boom():
        raise ValueError("nope")

    with pytest.raises(ValueError):
        boom.delay()


def test_eager_does_not_propagate_when_disabled_but_get_raises():
    app = Celery("t6", broker_url="memory://", result_backend="memory://")
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = False

    @app.task
    def boom2():
        raise RuntimeError("bad")

    r = boom2.delay()
    assert r.failed()
    with pytest.raises(RuntimeError):
        r.get(timeout=0.1)


def test_non_eager_timeout_and_eventual_success():
    app = Celery("t7", broker_url="memory://", result_backend="memory://")
    app.conf.task_always_eager = False

    @app.task
    def sleepy(t):
        time.sleep(t)
        return "ok"

    r = sleepy.delay(0.2)
    with pytest.raises(TimeoutError):
        r.get(timeout=0.05, interval=0.01)
    assert r.get(timeout=2) == "ok"