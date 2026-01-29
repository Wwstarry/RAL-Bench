"""
Minimal configuration handling for a Celery-like app.
"""

class Config(dict):
    """
    A dict-like config object with default values.
    """

    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)
        self.setdefault("broker_url", "memory://")
        self.setdefault("result_backend", "memory://")
        self.setdefault("task_always_eager", True)
        self.setdefault("task_eager_propagates", True)
        self.setdefault("task_ignore_result", False)
        self.setdefault("task_store_eager_result", True)

    def update(self, other=None, **kwargs):
        if other:
            super(Config, self).update(other)
        if kwargs:
            super(Config, self).update(kwargs)