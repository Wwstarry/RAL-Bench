"""
Public re-exports for *watchdog.observers*.

The reference library exposes ``Observer`` directly at this package level;
tests expect the same.
"""
from .api import Observer

__all__ = ["Observer"]