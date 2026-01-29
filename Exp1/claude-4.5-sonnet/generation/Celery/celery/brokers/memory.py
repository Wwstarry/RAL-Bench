"""
In-memory message broker
"""

import queue
import threading
from typing import Any, Dict, Optional
from celery.brokers.base import BaseBroker


class MemoryBroker(BaseBroker):
    """In-memory message broker for testing"""
    
    def __init__(self):
        self._queue = queue.Queue()
    
    def publish(self, message: Dict[str, Any]):
        """Publish a task message"""
        self._queue.put(message)
    
    def consume(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Consume a task message"""
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None