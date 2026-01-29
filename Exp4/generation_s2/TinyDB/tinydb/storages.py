from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict, Optional


class Storage:
    def read(self) -> Dict[str, Any]:
        raise NotImplementedError

    def write(self, data: Dict[str, Any]) -> None:
        raise NotImplementedError

    def close(self) -> None:
        return None


class JSONStorage(Storage):
    """
    Simple JSON file storage with atomic writes.

    - Creates file/directories if needed.
    - Uses a temp file + replace for atomic-ish updates.
    """

    def __init__(
        self,
        path: str,
        *,
        indent: Optional[int] = 2,
        sort_keys: bool = True,
        ensure_ascii: bool = False,
    ) -> None:
        self._path = path
        self._indent = indent
        self._sort_keys = sort_keys
        self._ensure_ascii = ensure_ascii

        parent = os.path.dirname(os.path.abspath(path))
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

        if not os.path.exists(self._path):
            self.write({})

    @property
    def path(self) -> str:
        return self._path

    def read(self) -> Dict[str, Any]:
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                raw = f.read().strip()
                if not raw:
                    return {}
                data = json.loads(raw)
                return data if isinstance(data, dict) else {}
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            # If corrupted, do not crash; treat as empty.
            return {}

    def write(self, data: Dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise TypeError("storage data must be a dict")

        directory = os.path.dirname(os.path.abspath(self._path)) or "."
        fd, tmp_path = tempfile.mkstemp(prefix=".tinydb-", suffix=".json", dir=directory, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    indent=self._indent,
                    sort_keys=self._sort_keys,
                    ensure_ascii=self._ensure_ascii,
                )
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self._path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass