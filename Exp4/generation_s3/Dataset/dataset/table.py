import sqlite3
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Set, Tuple, Union


def _quote_ident(name: str) -> str:
    if not isinstance(name, str) or name == "":
        raise ValueError("Identifier must be a non-empty string")
    if "\x00" in name:
        raise ValueError("NUL byte in identifier")
    # double up embedded quotes
    return '"' + name.replace('"', '""') + '"'


def _normalize_columns(columns: Union[str, Sequence[str]]) -> Tuple[str, ...]:
    if isinstance(columns, str):
        cols = (columns,)
    else:
        cols = tuple(columns)
    for c in cols:
        if not isinstance(c, str) or not c:
            raise ValueError("Invalid column name in index")
        if "\x00" in c:
            raise ValueError("NUL byte in column name")
    return cols


def _sqlite_type(value: Any) -> str:
    if value is None:
        return "TEXT"
    if isinstance(value, bool):
        return "INTEGER"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "REAL"
    if isinstance(value, (bytes, bytearray, memoryview)):
        return "BLOB"
    return "TEXT"


class Table:
    def __init__(self, db: "Any", name: str):
        self.db = db
        self.name = name

        self._exists_cache: Optional[bool] = None
        self._columns_cache: Optional[Set[str]] = None

        # internal registry: set of tuples of column names (order-sensitive)
        self._indexes: Set[Tuple[str, ...]] = set()
        self._indexes_introspected = False

    @property
    def _qname(self) -> str:
        return _quote_ident(self.name)

    def _table_exists(self) -> bool:
        if self._exists_cache is not None:
            return self._exists_cache
        cur = self.db.connection.cursor()
        try:
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
                (self.name,),
            )
            self._exists_cache = cur.fetchone() is not None
            return self._exists_cache
        finally:
            cur.close()

    def _ensure_table(self) -> None:
        if self._table_exists():
            return
        cur = self.db.connection.cursor()
        try:
            cur.execute(
                f"CREATE TABLE IF NOT EXISTS {self._qname} ("
                f"{_quote_ident('id')} INTEGER PRIMARY KEY AUTOINCREMENT)"
            )
        finally:
            cur.close()
        self._exists_cache = True
        self._columns_cache = None
        # If indexes were requested before table creation, create them now
        if self._indexes:
            for cols in sorted(self._indexes):
                self._create_sqlite_index(cols)

    def _refresh_columns(self) -> Set[str]:
        if not self._table_exists():
            return set()
        cur = self.db.connection.cursor()
        try:
            cur.execute(f"PRAGMA table_info({self._qname})")
            cols = {row[1] for row in cur.fetchall()}
            self._columns_cache = cols
            return cols
        finally:
            cur.close()

    @property
    def columns(self) -> Set[str]:
        if self._columns_cache is None:
            return self._refresh_columns()
        return set(self._columns_cache)

    def _ensure_columns_for_row(self, row: Mapping[str, Any]) -> None:
        self._ensure_table()
        existing = self.columns  # copy

        # Always keep 'id' present
        if "id" not in existing:
            self._columns_cache = None
            existing = self.columns

        to_add: List[Tuple[str, str]] = []
        for k, v in row.items():
            if k is None:
                continue
            if not isinstance(k, str) or k == "":
                raise ValueError("Column names must be non-empty strings")
            if "\x00" in k:
                raise ValueError("NUL byte in column name")
            if k in existing:
                continue
            if k == "id":
                # already created with table, but if cache stale, refresh
                continue
            to_add.append((k, _sqlite_type(v)))

        if not to_add:
            return

        cur = self.db.connection.cursor()
        try:
            for col, typ in to_add:
                cur.execute(f"ALTER TABLE {self._qname} ADD COLUMN {_quote_ident(col)} {typ}")
        finally:
            cur.close()
        self._columns_cache = None  # refresh lazily

        # Ensure any declared indexes that include new columns are created
        if self._indexes:
            for cols in list(self._indexes):
                # If index columns are now all present, ensure sqlite index exists
                if all(c in self.columns for c in cols):
                    self._create_sqlite_index(cols)

    def __len__(self) -> int:
        return self.count()

    def _where_clause(self, filters: Mapping[str, Any]) -> Tuple[str, Dict[str, Any], bool]:
        # returns (sql, params, valid)
        if not filters:
            return ("", {}, True)
        # if table doesn't exist, no rows
        if not self._table_exists():
            return ("", {}, False)
        cols = self.columns
        params: Dict[str, Any] = {}
        parts: List[str] = []
        i = 0
        for k, v in filters.items():
            if k not in cols:
                return ("", {}, False)
            pname = f"p{i}"
            i += 1
            parts.append(f"{_quote_ident(k)} = :{pname}")
            params[pname] = v
        return (" WHERE " + " AND ".join(parts), params, True)

    def insert(self, row: Mapping[str, Any]) -> Any:
        if row is None:
            raise ValueError("row must be a mapping")
        row = dict(row)
        self._ensure_columns_for_row(row)

        keys = [k for k in row.keys() if k is not None]
        if not keys:
            # Insert default row (only id)
            cur = self.db.connection.cursor()
            try:
                cur.execute(f"INSERT INTO {self._qname} DEFAULT VALUES")
                return cur.lastrowid
            finally:
                cur.close()

        cols_sql = ", ".join(_quote_ident(k) for k in keys)
        vals_sql = ", ".join(f":{k}" for k in keys)
        sql = f"INSERT INTO {self._qname} ({cols_sql}) VALUES ({vals_sql})"

        cur = self.db.connection.cursor()
        try:
            cur.execute(sql, row)
            return cur.lastrowid
        finally:
            cur.close()

    def insert_many(self, rows: Iterable[Mapping[str, Any]], chunk_size: Optional[int] = None) -> None:
        if chunk_size is None:
            chunk_size = 1000
        if chunk_size <= 0:
            chunk_size = 1000

        batch: List[Dict[str, Any]] = []
        for r in rows:
            if r is None:
                continue
            batch.append(dict(r))
            if len(batch) >= chunk_size:
                self._insert_many_batch(batch)
                batch.clear()
        if batch:
            self._insert_many_batch(batch)

    def _insert_many_batch(self, batch: List[Dict[str, Any]]) -> None:
        # evolve schema based on union of keys in batch
        union: Dict[str, Any] = {}
        for r in batch:
            for k, v in r.items():
                if k not in union and k is not None:
                    union[k] = v
        self._ensure_columns_for_row(union)

        # Use union keys for a stable prepared statement, but allow missing keys -> None
        keys = [k for k in union.keys() if k is not None]
        if not keys:
            # All empty rows: insert default values N times
            cur = self.db.connection.cursor()
            try:
                for _ in batch:
                    cur.execute(f"INSERT INTO {self._qname} DEFAULT VALUES")
            finally:
                cur.close()
            return

        cols_sql = ", ".join(_quote_ident(k) for k in keys)
        vals_sql = ", ".join(f":{k}" for k in keys)
        sql = f"INSERT INTO {self._qname} ({cols_sql}) VALUES ({vals_sql})"

        params_iter = ({k: r.get(k) for k in keys} for r in batch)

        cur = self.db.connection.cursor()
        try:
            cur.executemany(sql, list(params_iter))
        finally:
            cur.close()

    def update(self, row: Mapping[str, Any], keys: Union[str, Sequence[str]]) -> int:
        if row is None:
            raise ValueError("row must be a mapping")
        row = dict(row)
        key_cols = _normalize_columns(keys)

        for k in key_cols:
            if k not in row:
                raise ValueError(f"Missing key field: {k}")

        self._ensure_columns_for_row(row)

        set_cols = [c for c in row.keys() if c not in key_cols]
        if not set_cols:
            return 0

        set_sql = ", ".join(f"{_quote_ident(c)} = :set_{c}" for c in set_cols)
        where_sql = " AND ".join(f"{_quote_ident(k)} = :key_{k}" for k in key_cols)
        sql = f"UPDATE {self._qname} SET {set_sql} WHERE {where_sql}"

        params: Dict[str, Any] = {}
        for c in set_cols:
            params[f"set_{c}"] = row.get(c)
        for k in key_cols:
            params[f"key_{k}"] = row.get(k)

        cur = self.db.connection.cursor()
        try:
            cur.execute(sql, params)
            return int(cur.rowcount or 0)
        finally:
            cur.close()

    def upsert(self, row: Mapping[str, Any], keys: Union[str, Sequence[str]]) -> Any:
        if row is None:
            raise ValueError("row must be a mapping")
        row = dict(row)
        key_cols = _normalize_columns(keys)
        for k in key_cols:
            if k not in row:
                raise ValueError(f"Missing key field: {k}")

        # Ensure schema first
        self._ensure_columns_for_row(row)

        # Check existence
        filt = {k: row[k] for k in key_cols}
        existing = self.find_one(**filt)
        if existing is None:
            return self.insert(row)

        affected = self.update(row, key_cols)
        # Return a stable indicator; prefer existing id if present
        if isinstance(existing, Mapping) and "id" in existing:
            return existing.get("id")
        return affected

    def delete(self, **filters: Any) -> int:
        if not self._table_exists():
            return 0
        if not filters:
            sql = f"DELETE FROM {self._qname}"
            cur = self.db.connection.cursor()
            try:
                cur.execute(sql)
                return int(cur.rowcount or 0)
            finally:
                cur.close()

        where, params, valid = self._where_clause(filters)
        if not valid:
            return 0
        sql = f"DELETE FROM {self._qname}{where}"
        cur = self.db.connection.cursor()
        try:
            cur.execute(sql, params)
            return int(cur.rowcount or 0)
        finally:
            cur.close()

    def all(self) -> Iterator[Mapping[str, Any]]:
        return self.find()

    def find(self, **filters: Any) -> Iterator[Mapping[str, Any]]:
        if not self._table_exists():
            return iter(())
        where, params, valid = self._where_clause(filters)
        if not valid:
            return iter(())
        sql = f"SELECT * FROM {self._qname}{where}"
        cur = self.db.connection.cursor()
        try:
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description] if cur.description else []

            def gen() -> Iterator[Mapping[str, Any]]:
                try:
                    for r in cur:
                        yield {cols[i]: r[i] for i in range(len(cols))}
                finally:
                    cur.close()

            return gen()
        except sqlite3.OperationalError:
            cur.close()
            return iter(())
        except Exception:
            cur.close()
            raise

    def find_one(self, **filters: Any) -> Optional[Mapping[str, Any]]:
        if not self._table_exists():
            return None
        where, params, valid = self._where_clause(filters)
        if not valid:
            return None
        sql = f"SELECT * FROM {self._qname}{where} LIMIT 1"
        cur = self.db.connection.cursor()
        try:
            cur.execute(sql, params)
            row = cur.fetchone()
            if row is None:
                return None
            cols = [d[0] for d in cur.description] if cur.description else []
            return {cols[i]: row[i] for i in range(len(cols))}
        except sqlite3.OperationalError:
            return None
        finally:
            cur.close()

    def distinct(self, column: str) -> Iterator[Any]:
        if not isinstance(column, str) or not column:
            raise ValueError("column must be a non-empty string")
        if not self._table_exists():
            return iter(())
        if column not in self.columns:
            return iter(())
        sql = f"SELECT DISTINCT {_quote_ident(column)} FROM {self._qname}"
        cur = self.db.connection.cursor()
        try:
            cur.execute(sql)

            def gen() -> Iterator[Any]:
                try:
                    for r in cur:
                        yield r[0]
                finally:
                    cur.close()

            return gen()
        except sqlite3.OperationalError:
            cur.close()
            return iter(())
        except Exception:
            cur.close()
            raise

    def count(self, **filters: Any) -> int:
        if not self._table_exists():
            return 0
        where, params, valid = self._where_clause(filters)
        if not valid:
            return 0
        sql = f"SELECT COUNT(*) FROM {self._qname}{where}"
        cur = self.db.connection.cursor()
        try:
            cur.execute(sql, params)
            r = cur.fetchone()
            return int(r[0] if r else 0)
        except sqlite3.OperationalError:
            return 0
        finally:
            cur.close()

    def _introspect_indexes(self) -> None:
        if self._indexes_introspected:
            return
        self._indexes_introspected = True
        if not self._table_exists():
            return
        cur = self.db.connection.cursor()
        try:
            cur.execute(f"PRAGMA index_list({self._qname})")
            idx_rows = cur.fetchall()
            for idx in idx_rows:
                idx_name = idx[1]
                cur2 = self.db.connection.cursor()
                try:
                    cur2.execute(f"PRAGMA index_info({_quote_ident(idx_name)})")
                    info = cur2.fetchall()
                    cols = tuple(r[2] for r in info)
                    if cols:
                        self._indexes.add(cols)
                finally:
                    cur2.close()
        finally:
            cur.close()

    def has_index(self, columns: Union[str, Sequence[str]]) -> bool:
        cols = _normalize_columns(columns)
        self._introspect_indexes()
        return cols in self._indexes

    def create_index(self, columns: Union[str, Sequence[str]]) -> None:
        cols = _normalize_columns(columns)
        # Record internally regardless of table existence
        self._indexes.add(cols)

        if not self._table_exists():
            # Defer actual sqlite index creation until table exists and columns exist
            return

        # Ensure columns exist (if they don't, we cannot create an index yet; defer)
        table_cols = self.columns
        if not all(c in table_cols for c in cols):
            return

        self._create_sqlite_index(cols)

    def _create_sqlite_index(self, cols: Tuple[str, ...]) -> None:
        # idempotent creation: use IF NOT EXISTS with deterministic name
        idx_name = f"ix_{self.name}__" + "__".join(cols)
        q_idx_name = _quote_ident(idx_name)
        cols_sql = ", ".join(_quote_ident(c) for c in cols)
        sql = f"CREATE INDEX IF NOT EXISTS {q_idx_name} ON {self._qname} ({cols_sql})"
        cur = self.db.connection.cursor()
        try:
            cur.execute(sql)
        finally:
            cur.close()