# Minimal subset of celery._state
from .local import get_current_app as _get_current_app

def get_current_app():
    return _get_current_app()