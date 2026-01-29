"""
Table operations and data manipulation
"""


class Table:
    """
    Represents a database table with CRUD operations.
    """
    
    def __init__(self, database, name):
        """
        Initialize a table.
        
        Args:
            database: Database instance
            name: Table name
        """
        self.database = database
        self.name = name
        self._ensure_table()
    
    def _ensure_table(self):
        """Create the table if it doesn't exist."""
        if not self.database.table_exists(self.name):
            # Create table with id column
            sql = f"CREATE TABLE {self.name} (id INTEGER PRIMARY KEY AUTOINCREMENT)"
            self.database.execute(sql)
    
    def _ensure_columns(self, row):
        """
        Ensure all columns in the row exist in the table.
        
        Args:
            row: Dictionary representing a row
        """
        existing_columns = set(self.columns)
        
        for key in row.keys():
            if key not in existing_columns:
                # Add new column
                sql = f"ALTER TABLE {self.name} ADD COLUMN {key} TEXT"
                self.database.execute(sql)
                existing_columns.add(key)
    
    @property
    def columns(self):
        """
        Get list of column names.
        
        Returns:
            List of column names
        """
        return self.database.get_table_columns(self.name)
    
    def insert(self, row):
        """
        Insert a single row.
        
        Args:
            row: Dictionary representing the row
        
        Returns:
            True on success
        """
        if not row:
            return True
        
        self._ensure_columns(row)
        
        columns = list(row.keys())
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join(columns)
        
        sql = f"INSERT INTO {self.name} ({column_names}) VALUES ({placeholders})"
        values = [row[col] for col in columns]
        
        self.database.execute(sql, values)
        return True
    
    def insert_many(self, rows, chunk_size=None):
        """
        Insert multiple rows.
        
        Args:
            rows: Iterable of dictionaries
            chunk_size: Optional chunk size for batching (ignored in this implementation)
        
        Returns:
            Number of rows inserted
        """
        count = 0
        rows_list = list(rows)
        
        if not rows_list:
            return 0
        
        # Ensure all columns exist based on first row
        if rows_list:
            all_keys = set()
            for row in rows_list:
                all_keys.update(row.keys())
            
            if all_keys:
                sample_row = {k: None for k in all_keys}
                self._ensure_columns(sample_row)
        
        for row in rows_list:
            if row:
                columns = list(row.keys())
                placeholders = ', '.join(['?' for _ in columns])
                column_names = ', '.join(columns)
                
                sql = f"INSERT INTO {self.name} ({column_names}) VALUES ({placeholders})"
                values = [row[col] for col in columns]
                
                self.database.execute(sql, values)
                count += 1
        
        return count
    
    def update(self, row, keys):
        """
        Update rows matching the given keys.
        
        Args:
            row: Dictionary with updated values
            keys: List of column names to match on
        
        Returns:
            True on success
        """
        if not row or not keys:
            return True
        
        self._ensure_columns(row)
        
        # Separate update columns from key columns
        update_cols = [k for k in row.keys() if k not in keys]
        
        if not update_cols:
            return True
        
        set_clause = ', '.join([f"{col} = ?" for col in update_cols])
        where_clause = ' AND '.join([f"{key} = ?" for key in keys])
        
        sql = f"UPDATE {self.name} SET {set_clause} WHERE {where_clause}"
        values = [row[col] for col in update_cols] + [row[key] for key in keys]
        
        self.database.execute(sql, values)
        return True
    
    def upsert(self, row, keys):
        """
        Insert or update a row based on keys.
        
        Args:
            row: Dictionary representing the row
            keys: List of column names to match on
        
        Returns:
            True on success
        """
        if not row or not keys:
            return True
        
        self._ensure_columns(row)
        
        # Check if row exists
        where_clause = ' AND '.join([f"{key} = ?" for key in keys])
        where_values = [row[key] for key in keys]
        
        sql = f"SELECT COUNT(*) FROM {self.name} WHERE {where_clause}"
        cursor = self.database.execute(sql, where_values)
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            return self.update(row, keys)
        else:
            return self.insert(row)
    
    def delete(self, **filters):
        """
        Delete rows matching the filters.
        
        Args:
            **filters: Column-value pairs to filter on
        
        Returns:
            True on success
        """
        if not filters:
            # Delete all rows
            sql = f"DELETE FROM {self.name}"
            self.database.execute(sql)
        else:
            where_clause = ' AND '.join([f"{key} = ?" for key in filters.keys()])
            values = list(filters.values())
            
            sql = f"DELETE FROM {self.name} WHERE {where_clause}"
            self.database.execute(sql, values)
        
        return True
    
    def all(self):
        """
        Get all rows.
        
        Returns:
            List of dictionaries
        """
        sql = f"SELECT * FROM {self.name}"
        cursor = self.database.execute(sql)
        return [dict(row) for row in cursor]
    
    def find(self, **filters):
        """
        Find rows matching the filters.
        
        Args:
            **filters: Column-value pairs to filter on
        
        Returns:
            List of dictionaries
        """
        if not filters:
            return self.all()
        
        where_clause = ' AND '.join([f"{key} = ?" for key in filters.keys()])
        values = list(filters.values())
        
        sql = f"SELECT * FROM {self.name} WHERE {where_clause}"
        cursor = self.database.execute(sql, values)
        return [dict(row) for row in cursor]
    
    def find_one(self, **filters):
        """
        Find a single row matching the filters.
        
        Args:
            **filters: Column-value pairs to filter on
        
        Returns:
            Dictionary or None
        """
        results = self.find(**filters)
        return results[0] if results else None
    
    def distinct(self, column):
        """
        Get distinct values for a column.
        
        Args:
            column: Column name
        
        Returns:
            List of distinct values
        """
        sql = f"SELECT DISTINCT {column} FROM {self.name}"
        cursor = self.database.execute(sql)
        return [row[0] for row in cursor]
    
    def count(self, **filters):
        """
        Count rows matching the filters.
        
        Args:
            **filters: Column-value pairs to filter on
        
        Returns:
            Number of matching rows
        """
        if not filters:
            sql = f"SELECT COUNT(*) FROM {self.name}"
            cursor = self.database.execute(sql)
        else:
            where_clause = ' AND '.join([f"{key} = ?" for key in filters.keys()])
            values = list(filters.values())
            
            sql = f"SELECT COUNT(*) FROM {self.name} WHERE {where_clause}"
            cursor = self.database.execute(sql, values)
        
        return cursor.fetchone()[0]
    
    def __len__(self):
        """
        Get the number of rows in the table.
        
        Returns:
            Number of rows
        """
        return self.count()
    
    def create_index(self, columns):
        """
        Create an index on the specified columns.
        
        Args:
            columns: List of column names or single column name
        
        Returns:
            True on success
        """
        if isinstance(columns, str):
            columns = [columns]
        
        # Generate index name
        index_name = f"idx_{self.name}_{'_'.join(columns)}"
        column_list = ', '.join(columns)
        
        sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {self.name} ({column_list})"
        self.database.execute(sql)
        return True
    
    def has_index(self, columns):
        """
        Check if an index exists on the specified columns.
        
        Args:
            columns: List of column names or single column name
        
        Returns:
            True if index exists, False otherwise
        """
        if isinstance(columns, str):
            columns = [columns]
        
        # Get all indexes for this table
        sql = f"PRAGMA index_list({self.name})"
        cursor = self.database.execute(sql)
        indexes = cursor.fetchall()
        
        for index in indexes:
            index_name = index[1]
            
            # Get columns for this index
            sql = f"PRAGMA index_info({index_name})"
            cursor = self.database.execute(sql)
            index_columns = [row[2] for row in cursor]
            
            if index_columns == columns:
                return True
        
        return False