import logging

log = logging.getLogger(__name__)

class Table:
    def __init__(self, database, name):
        self.db = database
        self.name = name
        self._columns = None

    @property
    def columns(self):
        """List the columns in the table."""
        if self._columns is None:
            self._refresh_columns()
        return self._columns

    def _refresh_columns(self):
        """Query the database to update the internal column cache."""
        try:
            # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
            q = f"PRAGMA table_info(\"{self.name}\")"
            rows = list(self.db.query(q))
            self._columns = [r['name'] for r in rows]
        except Exception:
            self._columns = []

    def __len__(self):
        """Return the number of rows in the table."""
        try:
            q = f"SELECT COUNT(*) as c FROM \"{self.name}\""
            res = list(self.db.query(q))
            return res[0]['c'] if res else 0
        except Exception:
            # Table might not exist yet
            return 0

    def _ensure_table(self, row):
        """
        Ensure the table exists. If not, create it based on the keys in `row`.
        """
        if self.name in self.db.tables:
            return

        if not row:
            return

        columns_def = []
        for key, value in row.items():
            col_type = self._map_type(value)
            columns_def.append(f'"{key}" {col_type}')
        
        # If no ID provided, dataset usually adds an auto-increment integer ID.
        # We will assume if 'id' isn't in row, we create it.
        if 'id' not in row:
            columns_def.insert(0, '"id" INTEGER PRIMARY KEY AUTOINCREMENT')
        else:
            # If id is in row, we assume the user manages it, but we need to ensure
            # it's defined. If it was in the loop above, it's handled.
            pass

        cols_sql = ", ".join(columns_def)
        sql = f'CREATE TABLE IF NOT EXISTS "{self.name}" ({cols_sql})'
        self.db.query(sql)
        self._refresh_columns()

    def _ensure_columns(self, row):
        """
        Ensure all keys in `row` exist as columns in the table.
        Alter table to add missing columns.
        """
        current_cols = set(self.columns)
        new_cols = set(row.keys()) - current_cols
        
        for col in new_cols:
            col_type = self._map_type(row[col])
            sql = f'ALTER TABLE "{self.name}" ADD COLUMN "{col}" {col_type}'
            self.db.query(sql)
        
        if new_cols:
            self._refresh_columns()

    def _map_type(self, value):
        if isinstance(value, int):
            return "INTEGER"
        elif isinstance(value, float):
            return "REAL"
        elif isinstance(value, bool):
            return "INTEGER" # SQLite uses 0/1
        else:
            return "TEXT"

    def insert(self, row):
        """
        Insert a row into the table.
        
        Returns:
            The ID of the inserted row (if available).
        """
        return self.insert_many([row])

    def insert_many(self, rows, chunk_size=None):
        """
        Insert multiple rows.
        """
        if not rows:
            return
        
        # Normalize rows to dicts
        rows = [dict(r) for r in rows]
        
        # 1. Ensure table exists based on the first row (or union of keys if we were fancy, 
        #    but standard dataset often just looks at what's coming in).
        #    To be safe, we check schema against all keys in the batch.
        all_keys = set()
        for r in rows:
            all_keys.update(r.keys())
        
        # Create a dummy row with all keys to ensure schema
        dummy_schema_row = {k: rows[0].get(k) for k in all_keys}
        
        with self.db.lock:
            self._ensure_table(dummy_schema_row)
            self._ensure_columns(dummy_schema_row)

            # 2. Construct Insert SQL
            # We use the first row to determine the parameterized query structure,
            # but since we ensured columns for ALL keys, we can just use all_keys.
            keys = list(all_keys)
            placeholders = [f':{k}' for k in keys]
            columns_sql = ", ".join(f'"{k}"' for k in keys)
            values_sql = ", ".join(placeholders)
            
            sql = f'INSERT INTO "{self.name}" ({columns_sql}) VALUES ({values_sql})'
            
            cursor = self.db._conn.cursor()
            try:
                cursor.executemany(sql, rows)
                # Return the last row id
                return cursor.lastrowid
            finally:
                cursor.close()

    def update(self, row, keys):
        """
        Update a row based on the given keys.
        """
        if not isinstance(keys, (list, tuple)):
            keys = [keys]
            
        row = dict(row)
        with self.db.lock:
            self._ensure_table(row)
            self._ensure_columns(row)

            # Filter out keys from the update set, they are in the WHERE clause
            update_keys = [k for k in row.keys() if k not in keys]
            
            if not update_keys:
                return 0

            set_clause = ", ".join(f'"{k}" = :{k}' for k in update_keys)
            where_clause = " AND ".join(f'"{k}" = :{k}' for k in keys)
            
            sql = f'UPDATE "{self.name}" SET {set_clause} WHERE {where_clause}'
            
            cursor = self.db._conn.execute(sql, row)
            return cursor.rowcount

    def upsert(self, row, keys):
        """
        Update a row if it exists (based on keys), otherwise insert it.
        """
        if not isinstance(keys, (list, tuple)):
            keys = [keys]
        
        row = dict(row)
        
        # Try to update first
        # We need to check if the table exists first, otherwise update fails
        if self.name not in self.db.tables:
            self.insert(row)
            return

        # Check if the record exists
        filter_args = {k: row.get(k) for k in keys}
        existing = self.find_one(**filter_args)
        
        if existing:
            self.update(row, keys)
        else:
            self.insert(row)

    def delete(self, **filters):
        """
        Delete rows matching the filters.
        """
        with self.db.lock:
            if self.name not in self.db.tables:
                return 0

            if not filters:
                sql = f'DELETE FROM "{self.name}"'
                params = {}
            else:
                conditions = []
                for k in filters.keys():
                    conditions.append(f'"{k}" = :{k}')
                where_clause = " AND ".join(conditions)
                sql = f'DELETE FROM "{self.name}" WHERE {where_clause}'
                params = filters

            cursor = self.db._conn.execute(sql, params)
            return cursor.rowcount

    def _build_select(self, filters, limit=None, offset=None, order_by=None):
        if self.name not in self.db.tables:
            return None, None

        sql = f'SELECT * FROM "{self.name}"'
        params = {}
        
        if filters:
            conditions = []
            for k, v in filters.items():
                conditions.append(f'"{k}" = :{k}')
                params[k] = v
            sql += " WHERE " + " AND ".join(conditions)
        
        if order_by:
            # Basic order by handling. dataset allows ['-col'] for desc.
            clauses = []
            for item in (order_by if isinstance(order_by, list) else [order_by]):
                direction = "ASC"
                if item.startswith('-'):
                    direction = "DESC"
                    item = item[1:]
                clauses.append(f'"{item}" {direction}')
            sql += " ORDER BY " + ", ".join(clauses)

        if limit is not None:
            sql += f" LIMIT {int(limit)}"
            
        if offset is not None:
            sql += f" OFFSET {int(offset)}"
            
        return sql, params

    def find(self, **filters):
        """
        Find rows matching the filters.
        Special args: _limit, _offset, _step (not impl), _order_by
        """
        limit = filters.pop('_limit', None)
        offset = filters.pop('_offset', None)
        order_by = filters.pop('_order_by', None)
        
        sql, params = self._build_select(filters, limit, offset, order_by)
        if not sql:
            return iter([])
            
        return self.db.query(sql, **params)

    def find_one(self, **filters):
        """Find a single row."""
        filters['_limit'] = 1
        res = list(self.find(**filters))
        return res[0] if res else None

    def all(self):
        """Return all rows."""
        return self.find()

    def distinct(self, column, **filters):
        """Return distinct values for a column."""
        if self.name not in self.db.tables:
            return iter([])

        # Build WHERE clause
        where_clause = ""
        params = {}
        if filters:
            conditions = []
            for k, v in filters.items():
                conditions.append(f'"{k}" = :{k}')
                params[k] = v
            where_clause = " WHERE " + " AND ".join(conditions)

        sql = f'SELECT DISTINCT "{column}" FROM "{self.name}"{where_clause}'
        return self.db.query(sql, **params)

    def count(self, **filters):
        """Count rows matching filters."""
        if self.name not in self.db.tables:
            return 0

        where_clause = ""
        params = {}
        if filters:
            conditions = []
            for k, v in filters.items():
                conditions.append(f'"{k}" = :{k}')
                params[k] = v
            where_clause = " WHERE " + " AND ".join(conditions)

        sql = f'SELECT COUNT(*) as c FROM "{self.name}"{where_clause}'
        res = list(self.db.query(sql, **params))
        return res[0]['c']

    def create_index(self, columns, name=None):
        """Create an index on the specified columns."""
        if isinstance(columns, str):
            columns = [columns]
        
        if not name:
            sig = "_".join(columns)
            name = f"ix_{self.name}_{sig}"
            
        cols_sql = ", ".join(f'"{c}"' for c in columns)
        sql = f'CREATE INDEX IF NOT EXISTS "{name}" ON "{self.name}" ({cols_sql})'
        self.db.query(sql)

    def has_index(self, columns):
        """Check if an index exists for the given columns."""
        if isinstance(columns, str):
            columns = [columns]
        
        # Normalize columns to set for comparison
        target_cols = set(columns)
        
        # Query sqlite_master for indexes on this table
        q = f"PRAGMA index_list(\"{self.name}\")"
        indexes = list(self.db.query(q))
        
        for idx in indexes:
            # Get info for each index
            idx_name = idx['name']
            info_q = f"PRAGMA index_info(\"{idx_name}\")"
            info = list(self.db.query(info_q))
            # info returns seqno, cid, name
            idx_cols = set(r['name'] for r in info)
            
            if idx_cols == target_cols:
                return True
                
        return False