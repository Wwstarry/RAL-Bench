from __future__ import annotations

import json
import os
from typing import Optional


class Storage:
    """Minimal storage interface."""

    def read(self) -> dict | None:  # pragma: no cover
        raise NotImplementedError

    def write(self, data: dict) -> None:  # pragma: no cover
        raise NotImplementedError

    def close(self) -> None:  # pragma: no cover
        raise NotImplementedError


class JSONStorage(Storage):
    """File-based JSON document store."""

    def __init__(
        self,
        path: str,
        *,
        create_dirs: bool = True,
        encoding: str = "utf-8",
    ) -> None:
        self.path = path
        self._encoding = encoding
        self._create_dirs = create_dirs
        self._closed = False

        if self._create_dirs:
            parent = os.path.dirname(os.path.abspath(self.path))
            if parent:
                os.makedirs(parent, exist_ok=True)

    def read(self) -> Optional[dict]:
        if self._closed:
            raise ValueError("Storage is closed")

        if not os.path.exists(self.path):
            return None

        # Consider empty file as no data
        try:
            if os.path.getsize(self.path) == 0:
                return None
        except OSError:
            return None

        with open(self.path, "r", encoding=self._encoding) as f:
            raw = f.read()
            if raw.strip() == "":
                return None
            data = json.loads(raw)  # may raise JSONDecodeError
            if not isinstance(data, dict):
                raise ValueError("Database file must contain a JSON object (dict).")
            return data

    def write(self, data: dict) -> None:
        if self._closed:
            raise ValueError("Storage is closed")
        if not isinstance(data, dict):
            raise TypeError("Storage.write expects a dict")

        if self._create_dirs:
            parent = os.path.dirname(os.path.abspath(self.path))
            if parent:
                os.makedirs(parent, exist_ok=True)

        # Simple overwrite is acceptable per contract.
        tmp_path = f"{self.path}.tmp"
        payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
        with open(tmp_path, "w", encoding=self._encoding) as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, self.path)

    def close(self) -> None:
        self._closed = True