import sqlite3
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union

class Table:
    def __init__(self, database: 'Database', name: str):
        self.db = database
        self.name = name
        self._ensure_table()

    def _ensure_table(self):
        with self.db.conn:
            self.db.conn.execute(f"CREATE TABLE IF NOT EXISTS {self.name} (id INTEGER PRIMARY KEY AUTOINCREMENT)")

    def _ensure_columns(self, row: Dict[str, Any]):
        if not row:
            return

        cursor = self.db.conn.cursor()
        cursor.execute(f"PRAGMA table_info({self.name})")
        existing_columns = {row[1] for row in cursor.fetchall()}

        new_columns = set(row.keys()) - existing_columns
        for column in new_columns:
            self.db.conn.execute(f"ALTER TABLE {self.name} ADD COLUMN {column}")

    @property
    def columns(self) -> List[str]:
        cursor = self.db.conn.cursor()
        cursor.execute(f"PRAGMA table_info({self.name})")
        return [row[1] for row in cursor.fetchall()]

    def insert(self, row: Dict[str, Any]) -> int:
        self._ensure_columns(row)
        columns = ', '.join(row.keys())
        placeholders = ', '.join(['?'] * len(row))
        sql = f"INSERT INTO {self.name} ({columns}) VALUES ({placeholders})"
        cursor = self.db.conn.cursor()
        cursor.execute(sql, list(row.values()))
        return cursor.lastrowid

    def insert_many(self, rows: List[Dict[str, Any]], chunk_size: Optional[int] = None):
        if not rows:
            return

        self._ensure_columns(rows[0])
        columns = list(rows[0].keys())
        placeholders = ', '.join(['?'] * len(columns))
        sql = f"INSERT INTO {self.name} ({', '.join(columns)}) VALUES ({placeholders})"

        chunk_size = chunk_size or len(rows)
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i:i+chunk_size]
            values = [tuple(row.get(col) for col in columns) for row in chunk]
            self.db.conn.executemany(sql, values)

    def update(self, row: Dict[str, Any], keys: Dict[str, Any]) -> bool:
        if not keys:
            raise ValueError("At least one key must be provided for update")
        
        self._ensure_columns(row)
        set_clause = ', '.join(f"{k} = ?" for k in row.keys())
        where_clause = ' AND '.join(f"{k} = ?" for k in keys.keys())
        sql = f"UPDATE {self.name} SET {set_clause} WHERE {where_clause}"
        params = list(row.values()) + list(keys.values())
        
        cursor = self.db.conn.cursor()
        cursor.execute(sql, params)
        return cursor.rowcount > 0

    def upsert(self, row: Dict[str, Any], keys: Dict[str, Any]) -> bool:
        if self.update(row, keys):
            return True
        self.insert({**keys, **row})
        return True

    def delete(self, **filters: Any) -> bool:
        if not filters:
            raise ValueError("At least one filter must be provided for delete")
        
        where_clause = ' AND '.join(f"{k} = ?" for k in filters.keys())
        sql = f"DELETE FROM {self.name} WHERE {where_clause}"
        
        cursor = self.db.conn.cursor()
        cursor.execute(sql, list(filters.values()))
        return cursor.rowcount > 0

    def all(self) -> Iterator[Dict[str, Any]]:
        return self.find()

    def find(self, **filters: Any) -> Iterator[Dict[str, Any]]:
        where_clause = ' AND '.join(f"{k} = ?" for k in filters.keys()) if filters else '1=1'
        sql = f"SELECT * FROM {self.name} WHERE {where_clause}"
        cursor = self.db.conn.cursor()
        cursor.execute(sql, list(filters.values()))
        for row in cursor:
            yield dict(row)

    def find_one(self, **filters: Any) -> Optional[Dict[str, Any]]:
        try:
            return next(self.find(**filters))
        except StopIteration:
            return None

    def distinct(self, column: str) -> List[Any]:
        sql = f"SELECT DISTINCT {column} FROM {self.name}"
        cursor = self.db.conn.cursor()
        cursor.execute(sql)
        return [row[0] for row in cursor.fetchall()]

    def count(self, **filters: Any) -> int:
        where_clause = ' AND '.join(f"{k} = ?" for k in filters.keys()) if filters else '1=1'
        sql = f"SELECT COUNT(*) FROM {self.name} WHERE {where_clause}"
        cursor = self.db.conn.cursor()
        cursor.execute(sql, list(filters.values()))
        return cursor.fetchone()[0]

    def create_index(self, columns: Union[str, Sequence[str]]):
        if isinstance(columns, str):
            columns = [columns]
        
        index_name = f"idx_{self.name}_{'_'.join(columns)}"
        columns_str = ', '.join(columns)
        sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {self.name} ({columns_str})"
        self.db.conn.execute(sql)

    def has_index(self, columns: Union[str, Sequence[str]]) -> bool:
        if isinstance(columns, str):
            columns = [columns]
        
        cursor = self.db.conn.cursor()
        cursor.execute(f"PRAGMA index_list({self.name})")
        index_names = [row[1] for row in cursor.fetchall()]
        
        target_name = f"idx_{self.name}_{'_'.join(columns)}"
        return target_name in index_names

    def __len__(self) -> int:
        return self.count()