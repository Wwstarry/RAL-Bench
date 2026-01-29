from typing import Any, Dict, Optional, Tuple
from celery.brokers.base import BaseBroker
from collections import deque


class MemoryBroker(BaseBroker):
    def __init__(self):
        self._queue: deque = deque()
    
    def put_message(self, task_id: str, name: str, args: Tuple, kwargs: Dict) -> None:
        self._queue.append((task_id, name, args, kwargs))
    
    def get_message(self) -> Optional[Tuple[str, str, Tuple, Dict]]:
        if len(self._queue) == 0:
            return None
        return self._queue.popleft()