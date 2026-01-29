"""
Table operations and data access.
"""

import sqlite3
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union


class Table:
    """Table with CRUD operations."""
    
    def __init__(self, db: "Database", name: str):
        """
        Initialize table.
        
        Args:
            db: Database instance
            name: Table name
        """
        self.db = db
        self.name = name
        self._columns_cache: Optional[List[str]] = None
        self._ensure_table()
    
    def _ensure_table(self) -> None:
        """Create table if it doesn't exist."""
        sql = f"CREATE TABLE IF NOT EXISTS {self._quote(self.name)} (id INTEGER PRIMARY KEY AUTOINCREMENT)"
        self.db.execute(sql)
        self._columns_cache = None
    
    def _quote(self, identifier: str) -> str:
        """Quote SQL identifier."""
        return f'"{identifier}"'
    
    def _ensure_columns(self, row: Dict[str, Any]) -> None:
        """
        Ensure all columns in the row exist in the table.
        
        Args:
            row: Row dictionary
        """
        if not row:
            return
        
        columns = self.columns
        for key in row.keys():
            if key != "id" and key not in columns:
                self._add_column(key)
    
    def _add_column(self, column: str) -> None:
        """
        Add a column to the table.
        
        Args:
            column: Column name
        """
        sql = f"ALTER TABLE {self._quote(self.name)} ADD COLUMN {self._quote(column)}"
        try:
            self.db.execute(sql)
            self._columns_cache = None
        except sqlite3.OperationalError:
            # Column might already exist (race condition)
            pass
    
    @property
    def columns(self) -> List[str]:
        """Get list of column names."""
        if self._columns_cache is None:
            sql = f"PRAGMA table_info({self._quote(self.name)})"
            rows = list(self.db.query(sql))
            self._columns_cache = [row["name"] for row in rows]
        return self._columns_cache
    
    def insert(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a single row.
        
        Args:
            row: Row dictionary
            
        Returns:
            Inserted row with generated id
        """
        self._ensure_columns(row)
        
        if "id" in row:
            # Remove id to let autoincrement work
            row = row.copy()
            del row["id"]
        
        if not row:
            # Insert empty row to get an id
            sql = f"INSERT INTO {self._quote(self.name)} DEFAULT VALUES"
            cursor = self.db.execute(sql)
        else:
            columns = list(row.keys())
            placeholders = ", ".join(["?"] * len(columns))
            sql = f"INSERT INTO {self._quote(self.name)} ({', '.join(self._quote(c) for c in columns)}) VALUES ({placeholders})"
            cursor = self.db.execute(sql, tuple(row.values()))
        
        # Get the inserted row
        row_id = cursor.lastrowid
        return self.find_one(id=row_id)
    
    def insert_many(self, rows: List[Dict[str, Any]], chunk_size: Optional[int] = None) -> None:
        """
        Insert multiple rows efficiently.
        
        Args:
            rows: List of row dictionaries
            chunk_size: Chunk size for batch insertion (ignored in this implementation)
        """
        if not rows:
            return
        
        # Ensure all columns exist
        all_columns = set()
        for row in rows:
            all_columns.update(row.keys())
        
        for column in all_columns:
            if column != "id" and column not in self.columns:
                self._add_column(column)
        
        # Group rows by column sets for efficient insertion
        rows_by_columns: Dict[Tuple, List[Dict]] = {}
        for row in rows:
            # Remove id if present
            row_copy = row.copy()
            if "id" in row_copy:
                del row_copy["id"]
            
            columns = tuple(sorted(row_copy.keys()))
            rows_by_columns.setdefault(columns, []).append(row_copy)
        
        for columns, column_rows in rows_by_columns.items():
            if not columns:
                # Insert rows with no columns
                for _ in column_rows:
                    self.db.execute(f"INSERT INTO {self._quote(self.name)} DEFAULT VALUES")
            else:
                # Insert rows with same column set
                placeholders = ", ".join(["?"] * len(columns))
                sql = f"INSERT INTO {self._quote(self.name)} ({', '.join(self._quote(c) for c in columns)}) VALUES ({placeholders})"
                
                values = []
                for row in column_rows:
                    values.append(tuple(row[c] for c in columns))
                
                self.db.executemany(sql, values)
    
    def update(self, row: Dict[str, Any], keys: List[str]) -> None:
        """
        Update rows matching the given keys.
        
        Args:
            row: Row dictionary with new values
            keys: List of column names to match
        """
        if not keys:
            raise ValueError("keys cannot be empty")
        
        # Ensure columns exist
        self._ensure_columns(row)
        
        # Build WHERE clause
        where_parts = []
        params = []
        
        for key in keys:
            if key not in row:
                raise ValueError(f"Key '{key}' not found in row")
            where_parts.append(f"{self._quote(key)} = ?")
            params.append(row[key])
        
        # Build SET clause
        set_parts = []
        for key, value in row.items():
            if key not in keys:
                set_parts.append(f"{self._quote(key)} = ?")
                params.append(value)
        
        if not set_parts:
            return  # Nothing to update
        
        sql = f"UPDATE {self._quote(self.name)} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"
        self.db.execute(sql, params)
    
    def upsert(self, row: Dict[str, Any], keys: List[str]) -> Dict[str, Any]:
        """
        Update if exists, insert otherwise.
        
        Args:
            row: Row dictionary
            keys: List of column names to match
            
        Returns:
            Updated or inserted row
        """
        # Try to find existing row
        filters = {key: row[key] for key in keys if key in row}
        existing = self.find_one(**filters)
        
        if existing:
            # Update existing row
            self.update(row, keys)
            # Return updated row
            return self.find_one(id=existing["id"])
        else:
            # Insert new row
            return self.insert(row)
    
    def delete(self, **filters: Any) -> None:
        """
        Delete rows matching the filters.
        
        Args:
            **filters: Filter conditions
        """
        if not filters:
            # Delete all rows
            sql = f"DELETE FROM {self._quote(self.name)}"
            self.db.execute(sql)
            return
        
        where_parts = []
        params = []
        
        for key, value in filters.items():
            if value is None:
                where_parts.append(f"{self._quote(key)} IS NULL")
            else:
                where_parts.append(f"{self._quote(key)} = ?")
                params.append(value)
        
        sql = f"DELETE FROM {self._quote(self.name)} WHERE {' AND '.join(where_parts)}"
        self.db.execute(sql, params)
    
    def all(self) -> Iterator[Dict[str, Any]]:
        """
        Get all rows in the table.
        
        Yields:
            Rows as dictionaries
        """
        sql = f"SELECT * FROM {self._quote(self.name)}"
        yield from self.db.query(sql)
    
    def find(self, **filters: Any) -> Iterator[Dict[str, Any]]:
        """
        Find rows matching the filters.
        
        Args:
            **filters: Filter conditions
            
        Yields:
            Matching rows as dictionaries
        """
        if not filters:
            yield from self.all()
            return
        
        where_parts = []
        params = []
        
        for key, value in filters.items():
            if value is None:
                where_parts.append(f"{self._quote(key)} IS NULL")
            else:
                where_parts.append(f"{self._quote(key)} = ?")
                params.append(value)
        
        sql = f"SELECT * FROM {self._quote(self.name)} WHERE {' AND '.join(where_parts)}"
        yield from self.db.query(sql, *params)
    
    def find_one(self, **filters: Any) -> Optional[Dict[str, Any]]:
        """
        Find a single row matching the filters.
        
        Args:
            **filters: Filter conditions
            
        Returns:
            Matching row or None
        """
        for row in self.find(**filters):
            return row
        return None
    
    def distinct(self, column: str) -> List[Any]:
        """
        Get distinct values for a column.
        
        Args:
            column: Column name
            
        Returns:
            List of distinct values
        """
        sql = f"SELECT DISTINCT {self._quote(column)} FROM {self._quote(self.name)} WHERE {self._quote(column)} IS NOT NULL"
        return [row[column] for row in self.db.query(sql)]
    
    def count(self, **filters: Any) -> int:
        """
        Count rows matching the filters.
        
        Args:
            **filters: Filter conditions
            
        Returns:
            Number of matching rows
        """
        if not filters:
            sql = f"SELECT COUNT(*) as count FROM {self._quote(self.name)}"
            row = next(self.db.query(sql))
            return row["count"]
        
        where_parts = []
        params = []
        
        for key, value in filters.items():
            if value is None:
                where_parts.append(f"{self._quote(key)} IS NULL")
            else:
                where_parts.append(f"{self._quote(key)} = ?")
                params.append(value)
        
        sql = f"SELECT COUNT(*) as count FROM {self._quote(self.name)} WHERE {' AND '.join(where_parts)}"
        row = next(self.db.query(sql, *params))
        return row["count"]
    
    def create_index(self, columns: List[str]) -> None:
        """
        Create an index on the specified columns.
        
        Args:
            columns: List of column names
        """
        if not columns:
            raise ValueError("columns cannot be empty")
        
        # Generate index name
        index_name = f"idx_{self.name}_{'_'.join(columns)}"
        
        # Check if index already exists
        if self.has_index(columns):
            return
        
        # Create index
        columns_quoted = ", ".join(self._quote(c) for c in columns)
        sql = f"CREATE INDEX {self._quote(index_name)} ON {self._quote(self.name)} ({columns_quoted})"
        self.db.execute(sql)
    
    def has_index(self, columns: List[str]) -> bool:
        """
        Check if an index exists on the specified columns.
        
        Args:
            columns: List of column names
            
        Returns:
            True if index exists
        """
        if not columns:
            return False
        
        # Get all indexes for this table
        sql = f"PRAGMA index_list({self._quote(self.name)})"
        indexes = list(self.db.query(sql))
        
        for index in indexes:
            index_name = index["name"]
            # Get columns for this index
            sql = f"PRAGMA index_info({self._quote(index_name)})"
            index_columns = [row["name"] for row in self.db.query(sql)]
            
            if sorted(index_columns) == sorted(columns):
                return True
        
        return False
    
    def __len__(self) -> int:
        """Get number of rows in the table."""
        return self.count()
    
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate over all rows in the table."""
        return self.all()