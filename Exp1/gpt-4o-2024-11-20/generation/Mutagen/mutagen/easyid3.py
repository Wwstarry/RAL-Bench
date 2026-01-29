import os
import json
from collections.abc import MutableMapping


class EasyID3(MutableMapping):
    def __init__(self, path=None):
        self._tags = {}
        self._file_path = path
        if path and os.path.exists(path):
            self._load_tags()

    def _load_tags(self):
        with open(self._file_path, "r", encoding="utf-8") as f:
            self._tags = json.load(f)

    def save(self, path=None):
        save_path = path or self._file_path
        if not save_path:
            raise ValueError("No file path specified for saving.")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self._tags, f, ensure_ascii=False, indent=2)

    def __getitem__(self, key):
        if key not in self._tags:
            raise KeyError(f"Key '{key}' not found in tags.")
        return self._tags[key]

    def __setitem__(self, key, value):
        if not isinstance(value, list):
            raise ValueError("Tag values must be a list of strings.")
        self._tags[key] = value

    def __delitem__(self, key):
        if key not in self._tags:
            raise KeyError(f"Key '{key}' not found in tags.")
        del self._tags[key]

    def __iter__(self):
        return iter(self._tags)

    def __len__(self):
        return len(self._tags)

    def items(self):
        return self._tags.items()

    def keys(self):
        return self._tags.keys()

    def values(self):
        return self._tags.values()