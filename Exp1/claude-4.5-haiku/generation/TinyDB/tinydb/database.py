"""
Main database module for TinyDB.
Handles database initialization, table management, and persistence.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from tinydb.table import Table
from tinydb.storages import JSONStorage


class TinyDB:
    """
    A lightweight JSON-based database for managing tasks and projects.
    """

    def __init__(self, path: str = "db.json"):
        """
        Initialize TinyDB instance.

        Args:
            path: Path to the JSON database file
        """
        self.path = Path(path)
        self.storage = JSONStorage(str(self.path))
        self._tables: Dict[str, Table] = {}
        self._load_tables()

    def _load_tables(self) -> None:
        """Load all tables from storage."""
        data = self.storage.read()
        for table_name in data.keys():
            self._tables[table_name] = Table(table_name, self.storage)

    def table(self, name: str) -> Table:
        """
        Get or create a table by name.

        Args:
            name: Name of the table

        Returns:
            Table instance
        """
        if name not in self._tables:
            self._tables[name] = Table(name, self.storage)
        return self._tables[name]

    def tables(self) -> List[str]:
        """
        Get list of all table names.

        Returns:
            List of table names
        """
        return list(self._tables.keys())

    def drop_table(self, name: str) -> None:
        """
        Drop a table from the database.

        Args:
            name: Name of the table to drop
        """
        if name in self._tables:
            del self._tables[name]
        data = self.storage.read()
        if name in data:
            del data[name]
        self.storage.write(data)

    def close(self) -> None:
        """Close the database and flush all data."""
        self.storage.flush()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()