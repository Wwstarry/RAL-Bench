from __future__ import annotations


class CeleryError(Exception):
    pass


class TimeoutError(CeleryError):
    pass


class Retry(CeleryError):
    def __init__(self, exc=None, countdown=None, **kwargs):
        super().__init__(str(exc) if exc is not None else "Retry")
        self.exc = exc
        self.countdown = countdown
        self.kwargs = kwargs