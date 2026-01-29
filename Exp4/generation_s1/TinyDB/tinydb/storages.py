from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Union


PathLike = Union[str, os.PathLike]


class Storage:
    def __init__(self, path: PathLike, **kwargs: Any):
        self.path = Path(path)

    def read(self) -> Dict[str, Any]:
        raise NotImplementedError

    def write(self, data: Dict[str, Any]) -> None:
        raise NotImplementedError

    def close(self) -> None:
        return None


class JSONStorage(Storage):
    def __init__(
        self,
        path: PathLike,
        *,
        encoding: str = "utf-8",
        indent: int = 2,
        ensure_ascii: bool = False,
        create_dirs: bool = True,
        atomic_write: bool = True,
    ):
        super().__init__(path)
        self.encoding = encoding
        self.indent = indent
        self.ensure_ascii = ensure_ascii
        self.create_dirs = create_dirs
        self.atomic_write = atomic_write

    def read(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            raw = self.path.read_text(encoding=self.encoding)
        except FileNotFoundError:
            return {}
        if raw.strip() == "":
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON database file: {self.path}") from e
        if not isinstance(data, dict):
            raise ValueError(f"Database root must be an object/dict: {self.path}")
        return data

    def write(self, data: Dict[str, Any]) -> None:
        if self.create_dirs:
            self.path.parent.mkdir(parents=True, exist_ok=True)

        serialized = json.dumps(
            data,
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
            sort_keys=True,
        )

        if not self.atomic_write:
            self.path.write_text(serialized, encoding=self.encoding)
            return

        # Atomic: write to temp in same directory then replace
        tmp_path: Optional[Path] = None
        try:
            fd, tmp_name = tempfile.mkstemp(
                prefix=self.path.name + ".",
                suffix=".tmp",
                dir=str(self.path.parent),
                text=True,
            )
            tmp_path = Path(tmp_name)
            with os.fdopen(fd, "w", encoding=self.encoding) as f:
                f.write(serialized)
                f.flush()
                os.fsync(f.fileno())
            os.replace(str(tmp_path), str(self.path))
        finally:
            if tmp_path is not None and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    def close(self) -> None:
        return None