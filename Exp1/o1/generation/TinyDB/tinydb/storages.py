import json
import os

class JSONStorage:
    """
    Simple JSON storage that reads/writes a dictionary to a JSON file on disk.
    """

    def __init__(self, path):
        self._path = path
        self._data = None

    def read(self):
        """
        Read JSON data from the file if it exists, otherwise return {}.
        """
        if os.path.exists(self._path):
            with open(self._path, 'r', encoding='utf-8') as f:
                try:
                    self._data = json.load(f)
                except json.JSONDecodeError:
                    self._data = {}
        else:
            self._data = {}
        return self._data

    def write(self, data):
        """
        Write the given data dictionary to the file in JSON format.
        """
        self._data = data
        with open(self._path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, indent=2)

    def close(self):
        """
        Close any open resources. (No-op in this storage.)
        """
        pass