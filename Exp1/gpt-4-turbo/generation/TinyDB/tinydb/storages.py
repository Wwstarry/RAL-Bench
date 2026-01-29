import json
import threading
from typing import Any, Dict, List, Optional

class JSONStorage:
    """
    Simple JSON file storage for TinyDB.
    Thread-safe for basic use.
    """

    def __init__(self, path: str):
        self.path = path
        self._lock = threading.RLock()
        self._data = None

    def read(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
            except FileNotFoundError:
                self._data = {}
            except json.JSONDecodeError:
                self._data = {}
            return self._data

    def write(self, data: Dict[str, Any]):
        with self._lock:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

    def close(self):
        pass  # For compatibility