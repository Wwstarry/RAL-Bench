from celery.app.base import Celery

# Version info
VERSION = (0, 1, 0)
__version__ = '.'.join(map(str, VERSION))

__all__ = ['Celery', 'shared_task']

def shared_task(*args, **kwargs):
    """Create shared tasks (tasks not bound to any app)."""
    from celery._state import current_app
    return current_app.task(*args, **kwargs)