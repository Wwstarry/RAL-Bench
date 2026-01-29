import sqlite3
import threading


class Table:
    def __init__(self, database, name):
        self._db = database
        self._name = name
        self._conn = database._conn
        self._lock = threading.RLock()
        self._ensure_table()

    def _ensure_table(self):
        # Check if table exists, create if not
        with self._lock:
            c = self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (self._name,),
            )
            if c.fetchone() is None:
                # Create empty table with an implicit id column
                self._conn.execute(f"CREATE TABLE {self._quote(self._name)} (id INTEGER PRIMARY KEY AUTOINCREMENT)")
                self._conn.commit()

    def _quote(self, identifier):
        # Simple quoting for identifiers
        if '"' in identifier:
            raise ValueError("Invalid identifier")
        return f'"{identifier}"'

    def _get_columns(self):
        # Return list of columns in the table
        c = self._conn.execute(f"PRAGMA table_info({self._quote(self._name)})")
        return [row["name"] for row in c]

    @property
    def columns(self):
        cols = self._get_columns()
        # Exclude implicit id column from columns property
        return [c for c in cols if c != "id"]

    def __len__(self):
        c = self._conn.execute(f"SELECT COUNT(*) FROM {self._quote(self._name)}")
        return c.fetchone()[0]

    def _add_columns(self, new_columns):
        # Add columns to table if they don't exist
        existing = set(self._get_columns())
        for col in new_columns:
            if col == "id":
                continue
            if col not in existing:
                # Add column as TEXT type by default
                with self._lock:
                    self._conn.execute(f"ALTER TABLE {self._quote(self._name)} ADD COLUMN {self._quote(col)} TEXT")
                    self._conn.commit()

    def insert(self, row):
        if not isinstance(row, dict):
            raise ValueError("Row must be a dict")
        keys = list(row.keys())
        if not keys:
            raise ValueError("Row must have at least one column")
        self._add_columns(keys)
        columns = ", ".join(self._quote(k) for k in keys)
        placeholders = ", ".join("?" for _ in keys)
        values = [str(row[k]) if row[k] is not None else None for k in keys]
        sql = f"INSERT INTO {self._quote(self._name)} ({columns}) VALUES ({placeholders})"
        with self._lock:
            cur = self._conn.execute(sql, values)
            if not self._db._transaction_active:
                self._conn.commit()
            return cur.lastrowid

    def insert_many(self, rows, chunk_size=None):
        rows = list(rows)
        if not rows:
            return
        keys = set()
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Each row must be a dict")
            keys.update(row.keys())
        keys = list(keys)
        self._add_columns(keys)
        columns = ", ".join(self._quote(k) for k in keys)
        placeholders = ", ".join("?" for _ in keys)

        def row_values(row):
            return [str(row.get(k)) if row.get(k) is not None else None for k in keys]

        if chunk_size is None:
            chunk_size = 1000

        with self._lock:
            for i in range(0, len(rows), chunk_size):
                chunk = rows[i : i + chunk_size]
                values = [row_values(r) for r in chunk]
                sql = f"INSERT INTO {self._quote(self._name)} ({columns}) VALUES ({placeholders})"
                self._conn.executemany(sql, values)
            if not self._db._transaction_active:
                self._conn.commit()

    def update(self, row, keys):
        if not isinstance(row, dict):
            raise ValueError("Row must be a dict")
        if not keys:
            raise ValueError("Keys must be provided for update")
        keys = list(keys)
        self._add_columns(row.keys())
        set_keys = [k for k in row.keys() if k not in keys]
        if not set_keys:
            # Nothing to update
            return 0
        set_clause = ", ".join(f"{self._quote(k)}=?" for k in set_keys)
        where_clause = " AND ".join(f"{self._quote(k)}=?" for k in keys)
        sql = f"UPDATE {self._quote(self._name)} SET {set_clause} WHERE {where_clause}"
        values = [str(row[k]) if row[k] is not None else None for k in set_keys]
        values.extend(str(row[k]) if row[k] is not None else None for k in keys)
        with self._lock:
            cur = self._conn.execute(sql, values)
            if not self._db._transaction_active:
                self._conn.commit()
            return cur.rowcount

    def upsert(self, row, keys):
        if not keys:
            raise ValueError("Keys must be provided for upsert")
        keys = list(keys)
        # Check if row exists
        filters = {k: row[k] for k in keys if k in row}
        if len(filters) < len(keys):
            raise ValueError("Row must contain all keys for upsert")
        existing = list(self.find(**filters))
        if existing:
            return self.update(row, keys)
        else:
            return self.insert(row)

    def delete(self, **filters):
        if not filters:
            # Delete all rows
            sql = f"DELETE FROM {self._quote(self._name)}"
            params = ()
        else:
            where_clause = " AND ".join(f"{self._quote(k)}=?" for k in filters)
            sql = f"DELETE FROM {self._quote(self._name)} WHERE {where_clause}"
            params = tuple(str(v) if v is not None else None for v in filters.values())
        with self._lock:
            cur = self._conn.execute(sql, params)
            if not self._db._transaction_active:
                self._conn.commit()
            return cur.rowcount

    def all(self):
        sql = f"SELECT * FROM {self._quote(self._name)}"
        c = self._conn.execute(sql)
        for row in c:
            d = dict(row)
            d.pop("id", None)
            yield d

    def find(self, **filters):
        if not filters:
            return self.all()
        where_clause = " AND ".join(f"{self._quote(k)}=?" for k in filters)
        sql = f"SELECT * FROM {self._quote(self._name)} WHERE {where_clause}"
        params = tuple(str(v) if v is not None else None for v in filters.values())
        c = self._conn.execute(sql, params)
        for row in c:
            d = dict(row)
            d.pop("id", None)
            yield d

    def find_one(self, **filters):
        if not filters:
            sql = f"SELECT * FROM {self._quote(self._name)} LIMIT 1"
            c = self._conn.execute(sql)
        else:
            where_clause = " AND ".join(f"{self._quote(k)}=?" for k in filters)
            sql = f"SELECT * FROM {self._quote(self._name)} WHERE {where_clause} LIMIT 1"
            params = tuple(str(v) if v is not None else None for v in filters.values())
            c = self._conn.execute(sql, params)
        row = c.fetchone()
        if row is None:
            return None
        d = dict(row)
        d.pop("id", None)
        return d

    def distinct(self, column):
        if not column:
            raise ValueError("Column name required for distinct")
        # Ensure column exists
        if column not in self._get_columns():
            return []
        sql = f"SELECT DISTINCT {self._quote(column)} FROM {self._quote(self._name)}"
        c = self._conn.execute(sql)
        return [row[0] for row in c]

    def count(self, **filters):
        if not filters:
            sql = f"SELECT COUNT(*) FROM {self._quote(self._name)}"
            c = self._conn.execute(sql)
        else:
            where_clause = " AND ".join(f"{self._quote(k)}=?" for k in filters)
            sql = f"SELECT COUNT(*) FROM {self._quote(self._name)} WHERE {where_clause}"
            params = tuple(str(v) if v is not None else None for v in filters.values())
            c = self._conn.execute(sql, params)
        return c.fetchone()[0]

    def create_index(self, columns):
        if not columns:
            raise ValueError("Columns required to create index")
        if isinstance(columns, str):
            columns = [columns]
        # Normalize columns list
        columns = list(columns)
        # Compose index name
        idx_name = f"idx_{self._name}_" + "_".join(columns)
        # Check if index exists
        if self.has_index(columns):
            return
        cols_quoted = ", ".join(self._quote(c) for c in columns)
        sql = f"CREATE INDEX {self._quote(idx_name)} ON {self._quote(self._name)} ({cols_quoted})"
        with self._lock:
            self._conn.execute(sql)
            if not self._db._transaction_active:
                self._conn.commit()

    def has_index(self, columns):
        if isinstance(columns, str):
            columns = [columns]
        columns = list(columns)
        # Query sqlite_master for indexes on this table
        c = self._conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name=?",
            (self._name,),
        )
        target_cols = tuple(columns)
        for row in c:
            sql = row["sql"]
            if not sql:
                continue
            # Parse columns from sql: CREATE INDEX idx_name ON table_name (col1, col2)
            start = sql.find("(")
            end = sql.find(")")
            if start == -1 or end == -1:
                continue
            cols_str = sql[start + 1 : end]
            idx_cols = tuple(c.strip().strip('"') for c in cols_str.split(","))
            if idx_cols == target_cols:
                return True
        return False