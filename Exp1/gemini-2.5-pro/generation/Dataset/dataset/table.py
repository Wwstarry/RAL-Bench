import collections.abc
import sqlite3

def quote(name):
    """Quote an SQL identifier."""
    if not isinstance(name, str) or '"' in name or '`' in name:
        raise ValueError(f"Invalid identifier: {name}")
    return f'"{name}"'

def get_sqlite_type(value):
    """Determine the SQLite type for a given Python value."""
    if value is None:
        return "TEXT"
    if isinstance(value, bool):
        return "INTEGER"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "REAL"
    if isinstance(value, bytes):
        return "BLOB"
    return "TEXT"


class Table:
    """
    Represents a table in the database.
    """
    def __init__(self, database, name):
        self.db = database
        self.name = name
        self._quoted_name = quote(name)
        self._columns_cache = None
        self._table_exists_cache = None

    def _get_columns(self):
        """Get column names from the database, caching the result."""
        if self._columns_cache is None:
            try:
                cursor = self.db.conn.execute(f"PRAGMA table_info({self._quoted_name})")
                self._columns_cache = {row['name'] for row in cursor}
            except sqlite3.OperationalError:
                self._columns_cache = set()
        return self._columns_cache

    def _table_exists(self):
        """Check if the table exists in the database."""
        if self._table_exists_cache is None:
            cursor = self.db.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (self.name,)
            )
            self._table_exists_cache = cursor.fetchone() is not None
        return self._table_exists_cache

    def _ensure_table_and_columns(self, row):
        """Lazily create table and add missing columns."""
        if not self._table_exists():
            pk_name = quote("id")
            cols = [f"{pk_name} INTEGER PRIMARY KEY AUTOINCREMENT"]
            for col_name, value in row.items():
                col_type = get_sqlite_type(value)
                cols.append(f"{quote(col_name)} {col_type}")
            
            sql = f"CREATE TABLE {self._quoted_name} ({', '.join(cols)})"
            self.db.conn.execute(sql)
            self._table_exists_cache = True
            self._columns_cache = set(row.keys()) | {'id'}
            return

        existing_columns = self._get_columns()
        new_columns = set(row.keys()) - existing_columns
        if new_columns:
            for col_name in sorted(list(new_columns)):
                col_type = get_sqlite_type(row[col_name])
                sql = f"ALTER TABLE {self._quoted_name} ADD COLUMN {quote(col_name)} {col_type}"
                self.db.conn.execute(sql)
            self._columns_cache = None

    def insert(self, row):
        """Insert a new row (a dictionary)."""
        if not isinstance(row, dict):
            raise TypeError("Row must be a dictionary")
        
        self._ensure_table_and_columns(row)
        
        keys = list(row.keys())
        quoted_keys = [quote(k) for k in keys]
        placeholders = ', '.join(['?'] * len(keys))
        values = [row[k] for k in keys]
        
        sql = f"INSERT INTO {self._quoted_name} ({', '.join(quoted_keys)}) VALUES ({placeholders})"
        cursor = self.db.conn.cursor()
        cursor.execute(sql, values)
        return cursor.lastrowid

    def insert_many(self, rows, chunk_size=None):
        """Insert multiple rows."""
        if not isinstance(rows, collections.abc.Iterable):
            raise TypeError("Rows must be an iterable")

        buffered_rows = list(rows)
        if not buffered_rows:
            return

        all_keys = set()
        for row in buffered_rows:
            if not isinstance(row, dict):
                raise TypeError("Each row must be a dictionary")
            all_keys.update(row.keys())
        
        if all_keys:
            dummy_row = {k: None for k in all_keys}
            self._ensure_table_and_columns(dummy_row)

        sorted_keys = sorted(list(all_keys))
        quoted_keys = [quote(k) for k in sorted_keys]
        placeholders = ', '.join(['?'] * len(sorted_keys))
        sql = f"INSERT INTO {self._quoted_name} ({', '.join(quoted_keys)}) VALUES ({placeholders})"

        def row_generator():
            for row in buffered_rows:
                yield tuple(row.get(k) for k in sorted_keys)

        cursor = self.db.conn.cursor()
        cursor.executemany(sql, row_generator())

    def update(self, row, keys):
        """Update a row."""
        if not keys:
            raise ValueError("keys for update must be specified")

        update_cols = {k: v for k, v in row.items() if k not in keys}
        if not update_cols:
            return False

        set_clauses = [f"{quote(k)} = ?" for k in update_cols.keys()]
        where_clauses = [f"{quote(k)} = ?" for k in keys]
        
        values = list(update_cols.values()) + [row.get(k) for k in keys]

        sql = f"UPDATE {self._quoted_name} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
        
        cursor = self.db.conn.cursor()
        cursor.execute(sql, values)
        return cursor.rowcount > 0

    def upsert(self, row, keys):
        """Update or insert a row."""
        if not keys:
            raise ValueError("keys for upsert must be specified")
        
        self._ensure_table_and_columns(row)
        
        if not self.has_index(keys):
            self.create_index(keys, unique=True)

        insert_keys = sorted(row.keys())
        quoted_insert_keys = [quote(k) for k in insert_keys]
        placeholders = ', '.join(['?'] * len(insert_keys))
        
        update_keys = sorted([k for k in row.keys() if k not in keys])
        quoted_conflict_keys = [quote(k) for k in keys]

        if not update_keys:
            sql = f"INSERT OR IGNORE INTO {self._quoted_name} ({', '.join(quoted_insert_keys)}) VALUES ({placeholders})"
        else:
            set_clauses = [f"{quote(k)} = excluded.{quote(k)}" for k in update_keys]
            sql = (
                f"INSERT INTO {self._quoted_name} ({', '.join(quoted_insert_keys)}) "
                f"VALUES ({placeholders}) "
                f"ON CONFLICT({', '.join(quoted_conflict_keys)}) DO UPDATE SET {', '.join(set_clauses)}"
            )
        
        values = [row.get(k) for k in insert_keys]
        self.db.conn.execute(sql, values)

    def delete(self, **filters):
        """Delete rows."""
        if not filters:
            sql = f"DELETE FROM {self._quoted_name}"
            params = []
        else:
            where_clauses, params = self._build_where(filters)
            sql = f"DELETE FROM {self._quoted_name} WHERE {where_clauses}"
        
        cursor = self.db.conn.cursor()
        cursor.execute(sql, params)
        return cursor.rowcount > 0

    def _build_where(self, filters):
        clauses = []
        params = []
        for key, value in filters.items():
            clauses.append(f"{quote(key)} = ?")
            params.append(value)
        return " AND ".join(clauses), params

    def find(self, **filters):
        """Find rows."""
        if not self._table_exists():
            return iter([])

        if not filters:
            sql = f"SELECT * FROM {self._quoted_name}"
            params = []
        else:
            where_clauses, params = self._build_where(filters)
            sql = f"SELECT * FROM {self._quoted_name} WHERE {where_clauses}"
        
        return self.db.query(sql, **dict(zip([k for k in filters.keys()], params)))

    def find_one(self, **filters):
        """Find a single row."""
        try:
            return next(iter(self.find(**filters)))
        except StopIteration:
            return None

    def all(self):
        """Return all rows."""
        return self.find()

    def count(self, **filters):
        """Count rows."""
        if not self._table_exists():
            return 0

        if not filters:
            sql = f"SELECT COUNT(*) as c FROM {self._quoted_name}"
            params = []
        else:
            where_clauses, params = self._build_where(filters)
            sql = f"SELECT COUNT(*) as c FROM {self._quoted_name} WHERE {where_clauses}"
        
        cursor = self.db.conn.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchone()
        return result['c'] if result else 0

    def __len__(self):
        return self.count()

    @property
    def columns(self):
        """Return a list of column names."""
        if not self._get_columns() and self._table_exists():
            self._columns_cache = None
        return sorted(list(self._get_columns()))

    def distinct(self, column):
        """Return distinct values for a column."""
        if not self._table_exists():
            return iter([])
        sql = f"SELECT DISTINCT {quote(column)} FROM {self._quoted_name}"
        return self.db.query(sql)

    def create_index(self, columns, unique=False):
        """Create an index."""
        if isinstance(columns, str):
            columns = [columns]
        
        if not columns:
            raise ValueError("At least one column is required to create an index.")

        safe_cols_str = '_'.join(columns)
        index_name = f"ix_{self.name}_{safe_cols_str}"
        quoted_index_name = quote(index_name)
        quoted_cols = [quote(c) for c in columns]
        
        unique_str = "UNIQUE" if unique else ""
        sql = f"CREATE {unique_str} INDEX IF NOT EXISTS {quoted_index_name} ON {self._quoted_name} ({', '.join(quoted_cols)})"
        
        self.db.conn.execute(sql)
        return True

    def has_index(self, columns):
        """Check if an index on the given columns exists."""
        if not self._table_exists():
            return False
        if isinstance(columns, str):
            columns = [columns]
        
        columns_to_find = sorted(columns)

        cursor = self.db.conn.execute(f"PRAGMA index_list({self._quoted_name})")
        indexes = cursor.fetchall()
        
        for index in indexes:
            index_name = index['name']
            if index_name.startswith('sqlite_autoindex_'):
                continue

            info_cursor = self.db.conn.execute(f"PRAGMA index_info({quote(index_name)})")
            index_cols = sorted([row['name'] for row in info_cursor])
            
            if index_cols == columns_to_find:
                return True
        return False

    def __repr__(self):
        return f"<Table({self.name})>"