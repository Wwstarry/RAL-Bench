import io
import json
import os
import tempfile
from typing import Any, Dict, Optional


class Storage:
    def read(self) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def write(self, data: Dict[str, Any]) -> None:
        raise NotImplementedError

    def close(self) -> None:
        pass


class JSONStorage(Storage):
    def __init__(self, path: str, encoding: str = "utf-8", indent: int = 2, ensure_ascii: bool = False) -> None:
        self.path = os.path.abspath(path)
        self.encoding = encoding
        self.indent = indent
        self.ensure_ascii = ensure_ascii
        directory = os.path.dirname(self.path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        # Ensure file exists
        if not os.path.exists(self.path):
            # Initialize with empty database structure
            initial = {"tables": {}}
            self.write(initial)

    def read(self) -> Optional[Dict[str, Any]]:
        try:
            with io.open(self.path, "r", encoding=self.encoding) as f:
                content = f.read().strip()
                if not content:
                    return None
                return json.loads(content)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            # Corrupted/invalid file; return None so caller can re-init
            return None

    def write(self, data: Dict[str, Any]) -> None:
        directory = os.path.dirname(self.path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        # Atomic write: write to a temp file in the same directory and rename
        fd, tmp_path = tempfile.mkstemp(dir=directory or None, prefix=".tmp_tinydb_", suffix=".json")
        try:
            with io.open(fd, "w", encoding=self.encoding) as tmp_file:
                json.dump(data, tmp_file, indent=self.indent, ensure_ascii=self.ensure_ascii, sort_keys=True)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            # On POSIX, rename is atomic if same filesystem
            os.replace(tmp_path, self.path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                # If we can't remove the temp file, ignore
                pass

    def close(self) -> None:
        # Nothing to close for file-based JSON storage
        pass