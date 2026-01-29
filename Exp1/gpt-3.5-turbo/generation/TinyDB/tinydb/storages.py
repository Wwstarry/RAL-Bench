import json
import os
from threading import RLock


class JSONStorage:
    def __init__(self, path):
        """
        JSON file storage.

        :param path: path to JSON file.
        """
        self.path = path
        self._lock = RLock()

    def read(self):
        with self._lock:
            if not os.path.exists(self.path):
                return None
            with open(self.path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return None

    def write(self, data):
        with self._lock:
            tmp_path = self.path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self.path)