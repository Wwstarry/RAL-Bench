from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, Union
import sqlite3

SQLITE_TYPES = {
    int: "INTEGER",
    float: "REAL",
    bytes: "BLOB",
    str: "TEXT",
    bool: "INTEGER",  # store booleans as integers
}

def _sqlite_type_for_value(val: Any) -> str:
    if val is None:
        return "TEXT"
    for pytype, sqltype in SQLITE_TYPES.items():
        if isinstance(val, pytype):
            return sqltype
    return "TEXT"

def _quote_ident(name: str) -> str:
    # Quote sqlite identifier safely: wrap in double-quotes and escape existing quotes
    safe = name.replace('"', '""')
    return f'"{safe}"'

def _normalize_columns(columns: Union[str, Sequence[str]]) -> Tuple[str, ...]:
    if isinstance(columns, str):
        return (columns,)
    return tuple(columns)

class Table:
    """
    A minimal dataset-like table API on top of sqlite3 with lazy table creation and
    dynamic column addition upon insert.
    """

    def __init__(self, database, name: str):
        self.database = database
        self.name = name

    # Introspection
    @property
    def columns(self) -> List[str]:
        if not self._exists():
            return []
        cur = self.database._execute(f"PRAGMA table_info({_quote_ident(self.name)})")
        cols = [row[1] for row in cur.fetchall()]  # row[1] is 'name'
        return cols

    def __len__(self) -> int:
        return self.count()

    # Core mechanics
    def _exists(self) -> bool:
        cur = self.database._execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (self.name,),
        )
        return cur.fetchone() is not None

    def _ensure_table_exists(self, initial_columns: Optional[Dict[str, str]] = None) -> None:
        if self._exists():
            return
        # Create with a default auto-increment primary key 'id'
        colsdef = ['"id" INTEGER PRIMARY KEY AUTOINCREMENT']
        if initial_columns:
            for col, ctype in initial_columns.items():
                if col == "id":
                    # 'id' already defined as PK
                    continue
                colsdef.append(f'{_quote_ident(col)} {ctype}')
        sql = f"CREATE TABLE {_quote_ident(self.name)} ({', '.join(colsdef)})"
        self.database._execute(sql)

    def _ensure_columns(self, columns_types: Dict[str, str]) -> None:
        # Ensure table exists first
        self._ensure_table_exists(columns_types if not self._exists() else None)
        # Add any missing columns
        current_cols = set(self.columns)
        for col, ctype in columns_types.items():
            if col == "id":
                # 'id' already exists as PK
                continue
            if col not in current_cols:
                self.database._execute(
                    f"ALTER TABLE {_quote_ident(self.name)} ADD COLUMN {_quote_ident(col)} {ctype}"
                )
                current_cols.add(col)

    # Data modification
    def insert(self, row: Dict[str, Any]) -> Optional[int]:
        if row is None:
            return None
        cols_types: Dict[str, str] = {}
        for k, v in row.items():
            cols_types[k] = _sqlite_type_for_value(v)
        self._ensure_columns(cols_types)

        # Determine columns to include in insertion; don't include 'id' unless provided
        cols = [c for c in row.keys()]
        placeholders = ", ".join(["?"] * len(cols))
        collist = ", ".join(_quote_ident(c) for c in cols)
        sql = f"INSERT INTO {_quote_ident(self.name)} ({collist}) VALUES ({placeholders})"
        values = [row.get(c) for c in cols]
        cur = self.database._execute(sql, values)
        try:
            return cur.lastrowid
        except Exception:
            return None

    def insert_many(self, rows: Iterable[Dict[str, Any]], chunk_size: Optional[int] = None) -> None:
        rows = list(rows)
        if not rows:
            return None
        # Union of keys and infer types
        union_keys: List[str] = []
        types: Dict[str, str] = {}
        seen = set()
        for r in rows:
            for k, v in r.items():
                if k not in seen:
                    union_keys.append(k)
                    seen.add(k)
                if k not in types or types[k] == "TEXT":
                    t = _sqlite_type_for_value(v)
                    # Prefer non-TEXT if available
                    if types.get(k) in (None, "TEXT") and t != "TEXT":
                        types[k] = t
                    elif k not in types:
                        types[k] = t
        self._ensure_columns(types)
        # Prepare statement
        collist = ", ".join(_quote_ident(c) for c in union_keys)
        placeholders = ", ".join(["?"] * len(union_keys))
        sql = f"INSERT INTO {_quote_ident(self.name)} ({collist}) VALUES ({placeholders})"
        def gen_params():
            for r in rows:
                yield [r.get(c) for c in union_keys]
        if chunk_size and chunk_size > 0:
            # Execute in chunks
            buffer: List[List[Any]] = []
            for params in gen_params():
                buffer.append(params)
                if len(buffer) >= chunk_size:
                    self.database._executemany(sql, buffer)
                    buffer.clear()
            if buffer:
                self.database._executemany(sql, buffer)
        else:
            self.database._executemany(sql, gen_params())
        return None

    def update(self, row: Dict[str, Any], keys: Union[str, Sequence[str]]) -> int:
        key_cols = _normalize_columns(keys)
        if not key_cols:
            raise ValueError("update() requires 'keys' to identify rows to update.")
        # Ensure columns exist for any non-key columns
        col_types: Dict[str, str] = {}
        for k, v in row.items():
            col_types[k] = _sqlite_type_for_value(v)
        self._ensure_columns(col_types)

        set_cols = [c for c in row.keys() if c not in key_cols]
        if not set_cols:
            # Nothing to update; return 0
            return 0
        set_clause = ", ".join(f"{_quote_ident(c)}=?" for c in set_cols)
        where_clause_parts = []
        where_values: List[Any] = []
        for k in key_cols:
            if row.get(k) is None:
                where_clause_parts.append(f"{_quote_ident(k)} IS NULL")
            else:
                where_clause_parts.append(f"{_quote_ident(k)}=?")
                where_values.append(row.get(k))
        where_clause = " AND ".join(where_clause_parts)
        sql = f"UPDATE {_quote_ident(self.name)} SET {set_clause} WHERE {where_clause}"
        values = [row.get(c) for c in set_cols] + where_values
        cur = self.database._execute(sql, values)
        return cur.rowcount if cur.rowcount is not None else 0

    def upsert(self, row: Dict[str, Any], keys: Union[str, Sequence[str]]) -> Optional[int]:
        updated = self.update(row, keys)
        if updated > 0:
            # Updated existing rows; return None to indicate no new insert
            return None
        # No rows updated, insert new
        return self.insert(row)

    def delete(self, **filters) -> int:
        if not self._exists():
            return 0
        if not filters:
            cur = self.database._execute(f"DELETE FROM {_quote_ident(self.name)}")
            return cur.rowcount if cur.rowcount is not None else 0
        where_clause_parts = []
        values: List[Any] = []
        for k, v in filters.items():
            if v is None:
                where_clause_parts.append(f"{_quote_ident(k)} IS NULL")
            else:
                where_clause_parts.append(f"{_quote_ident(k)}=?")
                values.append(v)
        sql = f"DELETE FROM {_quote_ident(self.name)} WHERE " + " AND ".join(where_clause_parts)
        cur = self.database._execute(sql, values)
        return cur.rowcount if cur.rowcount is not None else 0

    # Query methods
    def all(self) -> Iterator[Dict[str, Any]]:
        if not self._exists():
            return iter(())
        sql = f"SELECT * FROM {_quote_ident(self.name)}"
        for row in self.database.query(sql):
            yield row

    def find(self, **filters) -> Iterator[Dict[str, Any]]:
        if not self._exists():
            return iter(())
        if not filters:
            return self.all()
        where_clause_parts = []
        values: List[Any] = []
        for k, v in filters.items():
            if v is None:
                where_clause_parts.append(f"{_quote_ident(k)} IS NULL")
            else:
                where_clause_parts.append(f"{_quote_ident(k)}=?")
                values.append(v)
        sql = f"SELECT * FROM {_quote_ident(self.name)} WHERE " + " AND ".join(where_clause_parts)
        cur = self.database._execute(sql, values)
        for row in cur:
            yield dict(row)

    def find_one(self, **filters) -> Optional[Dict[str, Any]]:
        if not self._exists():
            return None
        if not filters:
            sql = f"SELECT * FROM {_quote_ident(self.name)} LIMIT 1"
            cur = self.database._execute(sql)
            row = cur.fetchone()
            return dict(row) if row else None
        where_clause_parts = []
        values: List[Any] = []
        for k, v in filters.items():
            if v is None:
                where_clause_parts.append(f"{_quote_ident(k)} IS NULL")
            else:
                where_clause_parts.append(f"{_quote_ident(k)}=?")
                values.append(v)
        sql = f"SELECT * FROM {_quote_ident(self.name)} WHERE " + " AND ".join(where_clause_parts) + " LIMIT 1"
        cur = self.database._execute(sql, values)
        row = cur.fetchone()
        return dict(row) if row else None

    def distinct(self, column: str) -> List[Any]:
        if not self._exists():
            return []
        sql = f"SELECT DISTINCT {_quote_ident(column)} FROM {_quote_ident(self.name)}"
        cur = self.database._execute(sql)
        return [row[0] for row in cur.fetchall()]

    def count(self, **filters) -> int:
        if not self._exists():
            return 0
        if not filters:
            sql = f"SELECT COUNT(*) FROM {_quote_ident(self.name)}"
            cur = self.database._execute(sql)
            return int(cur.fetchone()[0])
        where_clause_parts = []
        values: List[Any] = []
        for k, v in filters.items():
            if v is None:
                where_clause_parts.append(f"{_quote_ident(k)} IS NULL")
            else:
                where_clause_parts.append(f"{_quote_ident(k)}=?")
                values.append(v)
        sql = f"SELECT COUNT(*) FROM {_quote_ident(self.name)} WHERE " + " AND ".join(where_clause_parts)
        cur = self.database._execute(sql, values)
        return int(cur.fetchone()[0])

    # Index helpers
    def create_index(self, columns: Union[str, Sequence[str]]) -> None:
        cols = _normalize_columns(columns)
        # Create table if not exists and ensure columns exist
        cols_types = {c: "TEXT" for c in cols}
        self._ensure_columns(cols_types)
        # Build deterministic index name
        idx_name = f"idx_{self.name}_{'_'.join(cols)}"
        sql = f"CREATE INDEX IF NOT EXISTS {_quote_ident(idx_name)} ON {_quote_ident(self.name)} ({', '.join(_quote_ident(c) for c in cols)})"
        self.database._execute(sql)

    def has_index(self, columns: Union[str, Sequence[str]]) -> bool:
        cols = _normalize_columns(columns)
        if not self._exists():
            return False
        # Find indexes on the table
        cur = self.database._execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?",
            (self.name,),
        )
        index_names = [row[0] for row in cur.fetchall()]
        for idx in index_names:
            try:
                info_cur = self.database._execute(f"PRAGMA index_info({_quote_ident(idx)})")
            except sqlite3.OperationalError:
                continue
            idx_cols = [row[2] for row in info_cur.fetchall()]  # 'name' of column
            if tuple(idx_cols) == tuple(cols):
                return True
        return False