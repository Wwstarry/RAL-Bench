import inspect

from ..result import AsyncResult


class Task:
    """
    Minimal Task base class.

    The Celery reference Task has many features; here we only implement what's
    required for local execution in tests.
    """

    abstract = True

    def __init__(self):
        self.app = None
        self.name = None
        self.__wrapped__ = None  # original function (for introspection)
        self.bind = False

    def run(self, *args, **kwargs):
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def delay(self, *args, **kwargs):
        return self.apply_async(args=args, kwargs=kwargs)

    def apply_async(self, args=None, kwargs=None, **options):
        args = args or ()
        kwargs = kwargs or {}
        return self.app._apply_task(self, args=args, kwargs=kwargs, **options)

    def signature(self, args=None, kwargs=None, **options):
        # Minimal placeholder; tests may not use.
        return (self.name, args or (), kwargs or {}, options)

    def __repr__(self):
        return f"<Task {self.name}>"

    # convenience helpers used by bound tasks in Celery
    @property
    def request(self):
        # Not implemented; provide a minimal object if accessed.
        return type("Request", (), {})()

    @staticmethod
    def _creates_bound_instance(fun):
        sig = inspect.signature(fun)
        params = list(sig.parameters.values())
        return bool(params) and params[0].name in ("self", "task")