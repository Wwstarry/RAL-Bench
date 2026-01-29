"""
Table access and manipulation.
"""

import sqlite3


class Table:
    """
    Represents a table in the database.
    """
    
    def __init__(self, database, name):
        """
        Initialize a table reference.
        
        Args:
            database: Database instance
            name: Table name
        """
        self.database = database
        self.name = name
        self._columns = None
        self._indexes = set()
    
    @property
    def columns(self):
        """
        Get the list of column names in this table.
        
        Returns:
            List of column names.
        """
        if self._columns is None:
            self._columns = self._get_columns()
        return self._columns
    
    def _get_columns(self):
        """Fetch column names from the table."""
        try:
            cursor = self.database._connection.execute(
                f"PRAGMA table_info({self.name})"
            )
            columns = [row[1] for row in cursor.fetchall()]
            return columns
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            return []
    
    def _refresh_columns(self):
        """Refresh the cached column list."""
        self._columns = None
    
    def _ensure_table_exists(self):
        """Ensure the table exists (create with a dummy column if needed)."""
        if not self._table_exists():
            # Create table with a dummy column that will be removed
            self.database.execute(
                f"CREATE TABLE {self.name} (id INTEGER PRIMARY KEY)"
            )
            self._refresh_columns()
    
    def _table_exists(self):
        """Check if the table exists in the database."""
        cursor = self.database.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (self.name,)
        )
        return cursor.fetchone() is not None
    
    def _add_column(self, column_name):
        """Add a new column to the table."""
        self.database.execute(
            f"ALTER TABLE {self.name} ADD COLUMN {column_name} TEXT"
        )
        self._refresh_columns()
    
    def insert(self, row):
        """
        Insert a single row into the table.
        
        Args:
            row: Dictionary of column names to values
        
        Returns:
            The last inserted row ID.
        """
        if not isinstance(row, dict):
            raise ValueError("Row must be a dictionary")
        
        self._ensure_table_exists()
        
        # Add any new columns
        for key in row.keys():
            if key not in self.columns:
                self._add_column(key)
        
        # Build INSERT statement
        columns = list(row.keys())
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join(columns)
        
        sql = f"INSERT INTO {self.name} ({column_names}) VALUES ({placeholders})"
        values = [row[col] for col in columns]
        
        cursor = self.database.execute(sql, values)
        return cursor.lastrowid
    
    def insert_many(self, rows, chunk_size=None):
        """
        Insert multiple rows into the table.
        
        Args:
            rows: Iterable of row dictionaries
            chunk_size: Optional batch size for commits
        
        Returns:
            List of inserted row IDs.
        """
        rows_list = list(rows)
        if not rows_list:
            return []
        
        self._ensure_table_exists()
        
        # Collect all columns from all rows
        all_columns = set()
        for row in rows_list:
            all_columns.update(row.keys())
        
        # Add any new columns
        for col in all_columns:
            if col not in self.columns:
                self._add_column(col)
        
        # Insert all rows
        row_ids = []
        for row in rows_list:
            row_id = self.insert(row)
            row_ids.append(row_id)
        
        return row_ids
    
    def update(self, row, keys):
        """
        Update rows matching the given key columns.
        
        Args:
            row: Dictionary of column names to values
            keys: List of column names to use as WHERE clause
        """
        if not isinstance(row, dict):
            raise ValueError("Row must be a dictionary")
        
        if not self._table_exists():
            return
        
        # Add any new columns
        for key in row.keys():
            if key not in self.columns:
                self._add_column(key)
        
        # Build WHERE clause from keys
        where_parts = []
        where_values = []
        for key in keys:
            where_parts.append(f"{key} = ?")
            where_values.append(row.get(key))
        
        where_clause = ' AND '.join(where_parts)
        
        # Build SET clause
        set_parts = []
        set_values = []
        for col, val in row.items():
            if col not in keys:
                set_parts.append(f"{col} = ?")
                set_values.append(val)
        
        if not set_parts:
            return
        
        set_clause = ', '.join(set_parts)
        
        sql = f"UPDATE {self.name} SET {set_clause} WHERE {where_clause}"
        self.database.execute(sql, set_values + where_values)
    
    def upsert(self, row, keys):
        """
        Insert or update a row (upsert operation).
        
        Args:
            row: Dictionary of column names to values
            keys: List of column names to use as unique identifier
        """
        if not isinstance(row, dict):
            raise ValueError("Row must be a dictionary")
        
        # Check if row exists
        existing = self.find_one(**{k: row.get(k) for k in keys})
        
        if existing:
            self.update(row, keys)
        else:
            self.insert(row)
    
    def delete(self, **filters):
        """
        Delete rows matching the given filters.
        
        Args:
            **filters: Column name to value mappings for WHERE clause
        """
        if not self._table_exists():
            return
        
        if not filters:
            # Delete all rows
            self.database.execute(f"DELETE FROM {self.name}")
            return
        
        # Build WHERE clause
        where_parts = []
        where_values = []
        for col, val in filters.items():
            where_parts.append(f"{col} = ?")
            where_values.append(val)
        
        where_clause = ' AND '.join(where_parts)
        sql = f"DELETE FROM {self.name} WHERE {where_clause}"
        self.database.execute(sql, where_values)
    
    def all(self):
        """
        Get all rows from the table.
        
        Yields:
            Row dictionaries.
        """
        if not self._table_exists():
            return
        
        cursor = self.database._connection.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute(f"SELECT * FROM {self.name}")
        
        for row in cursor.fetchall():
            yield dict(row)
    
    def find(self, **filters):
        """
        Find rows matching the given filters.
        
        Args:
            **filters: Column name to value mappings for WHERE clause
        
        Yields:
            Row dictionaries.
        """
        if not self._table_exists():
            return
        
        if not filters:
            # No filters, return all rows
            for row in self.all():
                yield row
            return
        
        # Build WHERE clause
        where_parts = []
        where_values = []
        for col, val in filters.items():
            where_parts.append(f"{col} = ?")
            where_values.append(val)
        
        where_clause = ' AND '.join(where_parts)
        sql = f"SELECT * FROM {self.name} WHERE {where_clause}"
        
        cursor = self.database._connection.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute(sql, where_values)
        
        for row in cursor.fetchall():
            yield dict(row)
    
    def find_one(self, **filters):
        """
        Find a single row matching the given filters.
        
        Args:
            **filters: Column name to value mappings for WHERE clause
        
        Returns:
            Row dictionary or None if not found.
        """
        for row in self.find(**filters):
            return row
        return None
    
    def distinct(self, column):
        """
        Get distinct values for a column.
        
        Args:
            column: Column name
        
        Yields:
            Distinct values.
        """
        if not self._table_exists():
            return
        
        sql = f"SELECT DISTINCT {column} FROM {self.name} ORDER BY {column}"
        cursor = self.database._connection.cursor()
        cursor.execute(sql)
        
        for row in cursor.fetchall():
            yield row[0]
    
    def count(self, **filters):
        """
        Count rows matching the given filters.
        
        Args:
            **filters: Column name to value mappings for WHERE clause
        
        Returns:
            Number of matching rows.
        """
        if not self._table_exists():
            return 0
        
        if not filters:
            sql = f"SELECT COUNT(*) FROM {self.name}"
            cursor = self.database._connection.cursor()
            cursor.execute(sql)
            return cursor.fetchone()[0]
        
        # Build WHERE clause
        where_parts = []
        where_values = []
        for col, val in filters.items():
            where_parts.append(f"{col} = ?")
            where_values.append(val)
        
        where_clause = ' AND '.join(where_parts)
        sql = f"SELECT COUNT(*) FROM {self.name} WHERE {where_clause}"
        
        cursor = self.database._connection.cursor()
        cursor.execute(sql, where_values)
        return cursor.fetchone()[0]
    
    def create_index(self, columns):
        """
        Create an index on the given columns.
        
        Args:
            columns: List of column names or a single column name
        """
        if isinstance(columns, str):
            columns = [columns]
        
        if not self._table_exists():
            return
        
        # Create a unique index name
        index_name = f"idx_{self.name}_{'_'.join(columns)}"
        column_list = ', '.join(columns)
        
        try:
            sql = f"CREATE INDEX {index_name} ON {self.name} ({column_list})"
            self.database.execute(sql)
            self._indexes.add(tuple(columns))
        except sqlite3.OperationalError:
            # Index might already exist
            pass
    
    def has_index(self, columns):
        """
        Check if an index exists on the given columns.
        
        Args:
            columns: List of column names or a single column name
        
        Returns:
            True if an index exists, False otherwise.
        """
        if isinstance(columns, str):
            columns = [columns]
        
        if not self._table_exists():
            return False
        
        columns_tuple = tuple(columns)
        
        # Check in-memory cache first
        if columns_tuple in self._indexes:
            return True
        
        # Query SQLite for indexes
        cursor = self.database.execute(
            "PRAGMA index_list(?)",
            (self.name,)
        )
        
        for index_row in cursor.fetchall():
            index_name = index_row[1]
            
            # Get columns for this index
            info_cursor = self.database.execute(
                "PRAGMA index_info(?)",
                (index_name,)
            )
            
            index_columns = tuple(row[2] for row in info_cursor.fetchall())
            
            if index_columns == columns_tuple:
                self._indexes.add(columns_tuple)
                return True
        
        return False
    
    def __len__(self):
        """
        Get the number of rows in the table.
        
        Returns:
            Number of rows.
        """
        return self.count()
    
    def __iter__(self):
        """
        Iterate over all rows in the table.
        
        Yields:
            Row dictionaries.
        """
        return self.all()