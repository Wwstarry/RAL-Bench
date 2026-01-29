import sqlite3

class Table:
    """
    A lightweight Table object representing an SQLite table and
    providing dataset-style methods.
    """

    def __init__(self, database, name):
        self._db = database
        self.name = name
        self._ensure_table()
        self._columns_cache = None

    def _ensure_table(self):
        """
        Lazily ensure the table exists with an 'id' primary key column.
        """
        sql = f"CREATE TABLE IF NOT EXISTS \"{self.name}\" (id INTEGER PRIMARY KEY AUTOINCREMENT)"
        self._db._connection.execute(sql)

    def _ensure_columns(self, row):
        """
        For all keys in the row, ensure that corresponding columns exist in the table.
        """
        existing_cols = self.columns  # This triggers a PRAGMA table_info
        for key in row.keys():
            if key not in existing_cols and key != 'id':
                # Add column, typed as TEXT by default
                alter_sql = f"ALTER TABLE \"{self.name}\" ADD COLUMN \"{key}\" TEXT"
                self._db._connection.execute(alter_sql)
                # Invalidate cache
                self._columns_cache = None

    @property
    def columns(self):
        """
        Return a list of columns for this table by querying PRAGMA table_info.
        """
        if self._columns_cache is None:
            cur = self._db._connection.execute(f'PRAGMA table_info("{self.name}")')
            self._columns_cache = [row['name'] for row in cur]
        return self._columns_cache

    def insert(self, row):
        """
        Insert a single row (dict) into the table.
        Returns the primary key of the inserted row if available.
        """
        self._ensure_columns(row)
        col_names = []
        placeholders = []
        values = []
        for k, v in row.items():
            col_names.append(f'"{k}"')
            placeholders.append(f':{k}')
            values.append(v)
        col_names_str = ", ".join(col_names)
        placeholders_str = ", ".join(placeholders)
        sql = f'INSERT INTO "{self.name}" ({col_names_str}) VALUES ({placeholders_str})'
        cur = self._db._connection.execute(sql, row)
        return cur.lastrowid

    def insert_many(self, rows, chunk_size=None):
        """
        Insert multiple rows. chunk_size is ignored in this implementation.
        """
        for row in rows:
            self.insert(row)

    def update(self, row, keys):
        """
        Update a row based on matching the provided keys.
        Only columns present in row (other than keys) are updated.
        """
        if not keys:
            return
        self._ensure_columns(row)

        set_parts = []
        where_parts = []
        params = {}

        for k, v in row.items():
            # Skip the key columns for UPDATE if we are using them for the WHERE clause
            if k not in keys:
                set_parts.append(f'"{k}" = :set_{k}')
                params[f'set_{k}'] = v
        for key_col in keys:
            where_parts.append(f'"{key_col}" = :where_{key_col}')
            params[f'where_{key_col}'] = row.get(key_col)

        if not set_parts:
            # Nothing to update
            return

        set_clause = ", ".join(set_parts)
        where_clause = " AND ".join(where_parts)
        sql = f'UPDATE "{self.name}" SET {set_clause} WHERE {where_clause}'
        self._db._connection.execute(sql, params)

    def upsert(self, row, keys):
        """
        Upsert the row based on the provided keys.
        If a matching row exists, it is updated, otherwise insert.
        """
        filters = {k: row[k] for k in keys if k in row}
        found = list(self.find(**filters))
        if found:
            self.update(row, keys)
        else:
            self.insert(row)

    def delete(self, **filters):
        """
        Delete rows matching the given filters.
        """
        if not filters:
            # If no filters, delete all
            sql = f'DELETE FROM "{self.name}"'
            self._db._connection.execute(sql)
            return

        where_parts = []
        for k in filters:
            where_parts.append(f'"{k}" = :{k}')
        where_clause = " AND ".join(where_parts)
        sql = f'DELETE FROM "{self.name}" WHERE {where_clause}'
        self._db._connection.execute(sql, filters)

    def all(self):
        """
        Yield all rows from the table as dictionaries.
        """
        sql = f'SELECT * FROM "{self.name}"'
        cur = self._db._connection.execute(sql)
        for row in cur:
            yield dict(row)

    def find(self, **filters):
        """
        Yield rows matching the given filters as dictionaries.
        """
        if not filters:
            yield from self.all()
            return

        where_parts = []
        for k in filters:
            where_parts.append(f'"{k}" = :{k}')
        where_clause = " AND ".join(where_parts)
        sql = f'SELECT * FROM "{self.name}" WHERE {where_clause}'
        cur = self._db._connection.execute(sql, filters)
        for row in cur:
            yield dict(row)

    def find_one(self, **filters):
        """
        Return the first row matching filters or None if none match.
        """
        if not filters:
            sql = f'SELECT * FROM "{self.name}" LIMIT 1'
            cur = self._db._connection.execute(sql)
        else:
            where_parts = []
            for k in filters:
                where_parts.append(f'"{k}" = :{k}')
            where_clause = " AND ".join(where_parts)
            sql = f'SELECT * FROM "{self.name}" WHERE {where_clause} LIMIT 1'
            cur = self._db._connection.execute(sql, filters)
        row = cur.fetchone()
        return dict(row) if row else None

    def distinct(self, column):
        """
        Yield distinct values for the given column.
        """
        sql = f'SELECT DISTINCT "{column}" FROM "{self.name}"'
        cur = self._db._connection.execute(sql)
        for row in cur:
            yield row[column]

    def count(self, **filters):
        """
        Return the count of rows matching the given filters.
        """
        if not filters:
            sql = f'SELECT COUNT(*) AS c FROM "{self.name}"'
            cur = self._db._connection.execute(sql)
            return cur.fetchone()['c']

        where_parts = []
        for k in filters:
            where_parts.append(f'"{k}" = :{k}')
        where_clause = " AND ".join(where_parts)
        sql = f'SELECT COUNT(*) AS c FROM "{self.name}" WHERE {where_clause}'
        cur = self._db._connection.execute(sql, filters)
        return cur.fetchone()['c']

    def create_index(self, columns):
        """
        Create an index on the given columns if not already present.
        """
        if not isinstance(columns, (list, tuple)):
            columns = [columns]
        index_name = f'ix_{self.name}_{"_".join(columns)}'
        # If it doesn't exist, we create it
        if not self.has_index(columns):
            cols_str = ", ".join([f'"{col}"' for col in columns])
            sql = f'CREATE INDEX "{index_name}" ON "{self.name}" ({cols_str})'
            self._db._connection.execute(sql)

    def has_index(self, columns):
        """
        Check if an index exists on exactly these columns (in any order).
        This is a simplified approach scanning the database indexes.
        """
        if not isinstance(columns, (list, tuple)):
            columns = [columns]
        wanted_cols = set(columns)

        # List all indexes:
        cur = self._db._connection.execute(f'PRAGMA index_list("{self.name}")')
        indexes = [dict(row) for row in cur]

        for idx_info in indexes:
            idx_name = idx_info['name']
            # gather columns for this index
            cur2 = self._db._connection.execute(f'PRAGMA index_info("{idx_name}")')
            indexed_cols = [dict(r)['name'] for r in cur2]
            if set(indexed_cols) == wanted_cols:
                return True
        return False

    def __len__(self):
        """
        Return the number of rows in the table.
        """
        return self.count()