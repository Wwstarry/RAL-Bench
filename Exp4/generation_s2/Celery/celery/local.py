# Minimal compatibility module; Celery provides thread-local current_app/current_task.
import threading

_local = threading.local()


def _set_current_app(app):
    _local.current_app = app


def get_current_app():
    return getattr(_local, "current_app", None)