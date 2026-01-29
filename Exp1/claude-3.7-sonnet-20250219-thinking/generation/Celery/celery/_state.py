# Global state for Celery
import threading

_tls = threading.local()

class _State:
    def __init__(self):
        self.app = None

    @property
    def current_app(self):
        if not hasattr(_tls, 'current_app'):
            from celery.app.base import Celery
            _tls.current_app = Celery()
        return _tls.current_app

    @current_app.setter
    def current_app(self, app):
        _tls.current_app = app

state = _State()

def get_current_app():
    return state.current_app

def set_current_app(app):
    state.current_app = app

# Proxy to current_app
current_app = state.current_app