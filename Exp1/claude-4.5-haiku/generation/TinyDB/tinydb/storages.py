"""
Storage module for persisting data to JSON files.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class JSONStorage:
    """
    JSON file-based storage backend.
    """

    def __init__(self, path: str):
        """
        Initialize JSON storage.

        Args:
            path: Path to the JSON file
        """
        self.path = Path(path)
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Ensure the JSON file exists and is valid."""
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.write({})
        else:
            try:
                with open(self.path, 'r') as f:
                    json.load(f)
            except (json.JSONDecodeError, IOError):
                self.write({})

    def read(self) -> Dict[str, Any]:
        """
        Read data from storage.

        Returns:
            Dictionary of stored data
        """
        try:
            with open(self.path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def write(self, data: Dict[str, Any]) -> None:
        """
        Write data to storage.

        Args:
            data: Dictionary to write
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=2)

    def flush(self) -> None:
        """Flush any pending writes (no-op for JSON storage)."""
        pass