from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, Optional


class StorageError(RuntimeError):
    pass


@dataclass
class JSONStorage:
    """
    Simple JSON file storage.

    Data format:
    {
      "_meta": { ... optional ... },
      "tables": {
        "tasks": {
          "_last_id": 12,
          "docs": {
            "1": {...},
            "2": {...}
          }
        }
      }
    }
    """
    path: str
    encoding: str = "utf-8"
    indent: int = 2
    ensure_ascii: bool = False
    fsync: bool = False

    def read(self) -> Dict[str, Any]:
        if not os.path.exists(self.path):
            return {"_meta": {}, "tables": {}}
        try:
            with open(self.path, "r", encoding=self.encoding) as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise StorageError("Root JSON must be an object")
            data.setdefault("_meta", {})
            data.setdefault("tables", {})
            if not isinstance(data["tables"], dict):
                raise StorageError('"tables" must be an object')
            return data
        except json.JSONDecodeError as e:
            raise StorageError(f"Invalid JSON in {self.path}: {e}") from e
        except OSError as e:
            raise StorageError(f"Failed reading {self.path}: {e}") from e

    def write(self, data: Dict[str, Any]) -> None:
        directory = os.path.dirname(os.path.abspath(self.path)) or "."
        os.makedirs(directory, exist_ok=True)

        fd: Optional[int] = None
        tmp_path: Optional[str] = None
        try:
            fd, tmp_path = tempfile.mkstemp(prefix=".tinydb-", suffix=".json", dir=directory)
            with os.fdopen(fd, "w", encoding=self.encoding) as f:
                json.dump(
                    data,
                    f,
                    indent=self.indent,
                    ensure_ascii=self.ensure_ascii,
                    sort_keys=True,
                )
                f.write("\n")
                f.flush()
                if self.fsync:
                    os.fsync(f.fileno())
            fd = None
            os.replace(tmp_path, self.path)
        except OSError as e:
            raise StorageError(f"Failed writing {self.path}: {e}") from e
        finally:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass