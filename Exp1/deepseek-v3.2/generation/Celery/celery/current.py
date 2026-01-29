"""
Current app context.
"""

import threading


class _Local(threading.local):
    """Thread-local storage."""
    
    def __init__(self):
        self.current_app = None


_local = _Local()


def _get_current_app():
    """Get current app."""
    return _local.current_app


def _set_current_app(app):
    """Set current app."""
    _local.current_app = app


class _CurrentApp:
    """Current app proxy."""
    
    @property
    def app(self):
        return _get_current_app()
    
    def _set_current_app(self, app):
        _set_current_app(app)
    
    def __getattr__(self, name):
        app = self.app
        if app is None:
            raise RuntimeError('No current app')
        return getattr(app, name)
    
    def __repr__(self):
        return f'<CurrentApp: {self.app}>'


current_app = _CurrentApp()