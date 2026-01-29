class CeleryError(Exception):
    pass


class TimeoutError(CeleryError):
    pass


class ImproperlyConfigured(CeleryError):
    pass


class TaskRevokedError(CeleryError):
    pass