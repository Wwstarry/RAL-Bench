import threading

class Table:
    """
    Represents a table in the database.
    """
    def __init__(self, database, name):
        self._db = database
        self._conn = database.connection
        self._name = name
        self._lock = threading.RLock()
        self._ensure_table_exists()
        self._indexes = set()

    def _ensure_table_exists(self):
        """
        Create the table if it does not exist.
        """
        with self._lock:
            sql = f"CREATE TABLE IF NOT EXISTS \"{self._name}\" (id INTEGER PRIMARY KEY AUTOINCREMENT)"
            self._conn.execute(sql)

    def _get_existing_columns(self):
        cursor = self._conn.execute(f"PRAGMA table_info(\"{self._name}\")")
        return set(row[1] for row in cursor)

    def _add_missing_columns(self, row):
        """
        Add columns to the table if they are missing.
        """
        existing = self._get_existing_columns()
        for key in row.keys():
            if key not in existing:
                # SQLite: add column as TEXT by default
                sql = f"ALTER TABLE \"{self._name}\" ADD COLUMN \"{key}\" TEXT"
                self._conn.execute(sql)

    def insert(self, row):
        """
        Insert a row (dict) into the table.
        """
        with self._lock:
            self._add_missing_columns(row)
            keys = list(row.keys())
            values = [row[k] for k in keys]
            placeholders = ", ".join(["?"] * len(keys))
            columns = ", ".join([f"\"{k}\"" for k in keys])
            sql = f"INSERT INTO \"{self._name}\" ({columns}) VALUES ({placeholders})"
            self._conn.execute(sql, values)

    def insert_many(self, rows, chunk_size=None):
        """
        Bulk insert rows.
        """
        rows = list(rows)
        if not rows:
            return
        with self._lock:
            self._add_missing_columns(rows[0])
            keys = list(rows[0].keys())
            columns = ", ".join([f"\"{k}\"" for k in keys])
            placeholders = ", ".join(["?"] * len(keys))
            sql = f"INSERT INTO \"{self._name}\" ({columns}) VALUES ({placeholders})"
            if chunk_size is None:
                chunk_size = len(rows)
            for i in range(0, len(rows), chunk_size):
                chunk = rows[i:i+chunk_size]
                values = [[row.get(k) for k in keys] for row in chunk]
                self._conn.executemany(sql, values)

    def update(self, row, keys):
        """
        Update rows matching keys with values from row.
        """
        with self._lock:
            self._add_missing_columns(row)
            set_keys = [k for k in row.keys() if k not in keys]
            set_clause = ", ".join([f"\"{k}\"=?" for k in set_keys])
            where_clause = " AND ".join([f"\"{k}\"=?" for k in keys])
            sql = f"UPDATE \"{self._name}\" SET {set_clause} WHERE {where_clause}"
            values = [row[k] for k in set_keys] + [row[k] for k in keys]
            self._conn.execute(sql, values)

    def upsert(self, row, keys):
        """
        Insert or update a row based on keys.
        """
        with self._lock:
            self._add_missing_columns(row)
            # Try update first
            where_clause = " AND ".join([f"\"{k}\"=?" for k in keys])
            select_sql = f"SELECT COUNT(*) FROM \"{self._name}\" WHERE {where_clause}"
            select_values = [row[k] for k in keys]
            cursor = self._conn.execute(select_sql, select_values)
            count = cursor.fetchone()[0]
            if count:
                self.update(row, keys)
            else:
                self.insert(row)

    def delete(self, **filters):
        """
        Delete rows matching filters.
        """
        with self._lock:
            if not filters:
                sql = f"DELETE FROM \"{self._name}\""
                self._conn.execute(sql)
            else:
                where_clause = " AND ".join([f"\"{k}\"=?" for k in filters.keys()])
                sql = f"DELETE FROM \"{self._name}\" WHERE {where_clause}"
                values = list(filters.values())
                self._conn.execute(sql, values)

    def all(self):
        """
        Return all rows as dicts.
        """
        with self._lock:
            cursor = self._conn.execute(f"SELECT * FROM \"{self._name}\"")
            columns = [desc[0] for desc in cursor.description]
            for row in cursor:
                yield dict(zip(columns, row))

    def find(self, **filters):
        """
        Find rows matching filters.
        """
        with self._lock:
            if not filters:
                return self.all()
            where_clause = " AND ".join([f"\"{k}\"=?" for k in filters.keys()])
            sql = f"SELECT * FROM \"{self._name}\" WHERE {where_clause}"
            values = list(filters.values())
            cursor = self._conn.execute(sql, values)
            columns = [desc[0] for desc in cursor.description]
            for row in cursor:
                yield dict(zip(columns, row))

    def find_one(self, **filters):
        """
        Find a single row matching filters.
        """
        with self._lock:
            where_clause = " AND ".join([f"\"{k}\"=?" for k in filters.keys()])
            sql = f"SELECT * FROM \"{self._name}\""
            values = []
            if filters:
                sql += f" WHERE {where_clause}"
                values = list(filters.values())
            cursor = self._conn.execute(sql, values)
            row = cursor.fetchone()
            if row is None:
                return None
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))

    def distinct(self, column):
        """
        Return distinct values for a column.
        """
        with self._lock:
            sql = f"SELECT DISTINCT \"{column}\" FROM \"{self._name}\""
            cursor = self._conn.execute(sql)
            return [row[0] for row in cursor]

    def count(self, **filters):
        """
        Count rows matching filters.
        """
        with self._lock:
            if not filters:
                sql = f"SELECT COUNT(*) FROM \"{self._name}\""
                cursor = self._conn.execute(sql)
                return cursor.fetchone()[0]
            where_clause = " AND ".join([f"\"{k}\"=?" for k in filters.keys()])
            sql = f"SELECT COUNT(*) FROM \"{self._name}\" WHERE {where_clause}"
            values = list(filters.values())
            cursor = self._conn.execute(sql, values)
            return cursor.fetchone()[0]

    def create_index(self, columns):
        """
        Create an index on the given columns.
        """
        if isinstance(columns, str):
            columns = [columns]
        idx_name = f"idx_{self._name}_" + "_".join(columns)
        cols_sql = ", ".join([f"\"{c}\"" for c in columns])
        with self._lock:
            sql = f"CREATE INDEX IF NOT EXISTS \"{idx_name}\" ON \"{self._name}\" ({cols_sql})"
            self._conn.execute(sql)
            self._indexes.add(tuple(columns))

    def has_index(self, columns):
        """
        Check if an index exists on the given columns.
        """
        if isinstance(columns, str):
            columns = [columns]
        idx_name = f"idx_{self._name}_" + "_".join(columns)
        with self._lock:
            cursor = self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=? AND name=?",
                (self._name, idx_name)
            )
            return cursor.fetchone() is not None

    @property
    def columns(self):
        """
        Return the list of column names.
        """
        with self._lock:
            cursor = self._conn.execute(f"PRAGMA table_info(\"{self._name}\")")
            return [row[1] for row in cursor]

    def __len__(self):
        """
        Return the number of rows in the table.
        """
        return self.count()