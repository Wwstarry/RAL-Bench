# dataset/table.py

import sqlite3

class Table:
    def __init__(self, connection, name):
        self.connection = connection
        self.name = name
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        self.connection.execute(f"CREATE TABLE IF NOT EXISTS {self.name} (id INTEGER PRIMARY KEY)")

    def insert(self, row):
        keys = row.keys()
        columns = ", ".join(keys)
        placeholders = ", ".join(f":{key}" for key in keys)
        self.connection.execute(f"INSERT INTO {self.name} ({columns}) VALUES ({placeholders})", row)

    def insert_many(self, rows, chunk_size=None):
        if not rows:
            return
        keys = rows[0].keys()
        columns = ", ".join(keys)
        placeholders = ", ".join(f":{key}" for key in keys)
        query = f"INSERT INTO {self.name} ({columns}) VALUES ({placeholders})"
        if chunk_size:
            for i in range(0, len(rows), chunk_size):
                self.connection.executemany(query, rows[i:i+chunk_size])
        else:
            self.connection.executemany(query, rows)

    def update(self, row, keys):
        set_clause = ", ".join(f"{key} = :{key}" for key in row.keys() if key not in keys)
        where_clause = " AND ".join(f"{key} = :{key}" for key in keys)
        query = f"UPDATE {self.name} SET {set_clause} WHERE {where_clause}"
        self.connection.execute(query, row)

    def upsert(self, row, keys):
        filters = {key: row[key] for key in keys}
        existing = self.find_one(**filters)
        if existing:
            self.update(row, keys)
        else:
            self.insert(row)

    def delete(self, **filters):
        where_clause = " AND ".join(f"{key} = :{key}" for key in filters.keys())
        query = f"DELETE FROM {self.name} WHERE {where_clause}"
        self.connection.execute(query, filters)

    def all(self):
        query = f"SELECT * FROM {self.name}"
        cursor = self.connection.execute(query)
        for row in cursor:
            yield dict(row)

    def find(self, **filters):
        where_clause = " AND ".join(f"{key} = :{key}" for key in filters.keys())
        query = f"SELECT * FROM {self.name} WHERE {where_clause}"
        cursor = self.connection.execute(query, filters)
        for row in cursor:
            yield dict(row)

    def find_one(self, **filters):
        where_clause = " AND ".join(f"{key} = :{key}" for key in filters.keys())
        query = f"SELECT * FROM {self.name} WHERE {where_clause} LIMIT 1"
        cursor = self.connection.execute(query, filters)
        row = cursor.fetchone()
        return dict(row) if row else None

    def distinct(self, column):
        query = f"SELECT DISTINCT {column} FROM {self.name}"
        cursor = self.connection.execute(query)
        return [row[column] for row in cursor]

    def count(self, **filters):
        where_clause = " AND ".join(f"{key} = :{key}" for key in filters.keys())
        query = f"SELECT COUNT(*) FROM {self.name} WHERE {where_clause}" if filters else f"SELECT COUNT(*) FROM {self.name}"
        cursor = self.connection.execute(query, filters)
        return cursor.fetchone()[0]

    def create_index(self, columns):
        index_name = f"idx_{self.name}_{'_'.join(columns)}"
        columns_clause = ", ".join(columns)
        query = f"CREATE INDEX IF NOT EXISTS {index_name} ON {self.name} ({columns_clause})"
        self.connection.execute(query)

    def has_index(self, columns):
        index_name = f"idx_{self.name}_{'_'.join(columns)}"
        query = f"PRAGMA index_list({self.name})"
        cursor = self.connection.execute(query)
        for row in cursor:
            if row["name"] == index_name:
                return True
        return False

    @property
    def columns(self):
        query = f"PRAGMA table_info({self.name})"
        cursor = self.connection.execute(query)
        return [row["name"] for row in cursor]

    def __len__(self):
        return self.count()