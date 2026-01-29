"""
This module contains the Table class, which represents a single
database table and provides methods for data manipulation and querying.
"""
import sqlalchemy
from sqlalchemy.schema import Table as SaTable, MetaData, Column, Index
from sqlalchemy.types import Integer, String, Float, Boolean
from sqlalchemy.dialects import sqlite

class Table(object):
    """
    Represents a table in the database.
    
    Provides methods to insert, update, and query data.
    Schema (columns) is created and modified automatically.
    """
    def __init__(self, database, name):
        self.database = database
        self.name = name
        self._table = None  # SQLAlchemy Table object, lazily loaded

    def _get_sa_table(self, conn=None):
        """Get the SQLAlchemy Table object, reflecting from DB if needed."""
        if self._table is None:
            try:
                self._table = SaTable(
                    self.name,
                    self.database.metadata,
                    autoload_with=conn or self.database.engine
                )
            except sqlalchemy.exc.NoSuchTableError:
                pass
        return self._table

    def _python_type_to_sql(self, value):
        """Infer SQLAlchemy type from a Python value."""
        if isinstance(value, bool):
            return Boolean
        if isinstance(value, int):
            return Integer
        if isinstance(value, float):
            return Float
        return String

    def _ensure_table_and_columns(self, row, conn):
        """Ensure table and columns exist for the given row data."""
        inspector = sqlalchemy.inspect(conn)
        if not inspector.has_table(self.name):
            columns = [Column('id', Integer, primary_key=True, autoincrement=True)]
            for col_name, value in row.items():
                col_type = self._python_type_to_sql(value)
                columns.append(Column(col_name, col_type))
            
            table = SaTable(self.name, self.database.metadata, *columns)
            table.create(conn)
            self._table = table
            return

        self._get_sa_table(conn)
        existing_columns = {c.name for c in self._table.columns}
        
        new_cols_exist = False
        for col_name, value in row.items():
            if col_name not in existing_columns:
                new_cols_exist = True
                col_type = self._python_type_to_sql(value)
                type_string = col_type().compile(self.database.engine.dialect)
                # Use raw SQL for ALTER TABLE for simplicity and broad compatibility
                sql = f'ALTER TABLE "{self.name}" ADD COLUMN "{col_name}" {type_string}'
                conn.execute(sqlalchemy.text(sql))
        
        if new_cols_exist:
            # Refresh metadata to see new columns
            self.database.metadata.clear()
            self._table = None
            self._get_sa_table(conn)

    def insert(self, row):
        """Insert a single row (dictionary) into the table."""
        conn = self.database._get_connection()
        try:
            self._ensure_table_and_columns(row, conn)
            sa_table = self._get_sa_table(conn)
            stmt = sa_table.insert().values(**row)
            result = conn.execute(stmt)
            if self.database._tx is None:
                if hasattr(conn, 'commit'): conn.commit()
            return result.inserted_primary_key[0]
        finally:
            if not self.database._tx:
                conn.close()

    def insert_many(self, rows, chunk_size=1000):
        """Insert multiple rows in chunks."""
        rows_iter = iter(rows)
        conn = self.database._get_connection()
        try:
            while True:
                chunk = [next(rows_iter) for _ in range(chunk_size)]
                if not chunk: break
                
                self._ensure_table_and_columns(chunk[0], conn)
                sa_table = self._get_sa_table(conn)
                conn.execute(sa_table.insert(), chunk)
            
            if self.database._tx is None:
                if hasattr(conn, 'commit'): conn.commit()
        except StopIteration:
            if self.database._tx is None:
                if hasattr(conn, 'commit'): conn.commit()
        finally:
            if not self.database._tx:
                conn.close()

    def update(self, row, keys):
        """Update a row identified by key(s)."""
        conn = self.database._get_connection()
        try:
            sa_table = self._get_sa_table(conn)
            if sa_table is None: return False

            keys = [keys] if not isinstance(keys, (list, tuple)) else keys
            filters = [sa_table.c[k] == row.get(k) for k in keys]
            values = {k: v for k, v in row.items() if k not in keys}
            if not values: return False

            stmt = sa_table.update().where(sqlalchemy.and_(*filters)).values(**values)
            result = conn.execute(stmt)
            if self.database._tx is None:
                if hasattr(conn, 'commit'): conn.commit()
            return result.rowcount > 0
        finally:
            if not self.database._tx:
                conn.close()

    def upsert(self, row, keys):
        """Insert a row or update it if it exists (based on keys)."""
        if self.database.engine.dialect.name != 'sqlite':
            raise NotImplementedError("Upsert is only implemented for SQLite.")

        conn = self.database._get_connection()
        try:
            if not self.has_index(keys, _conn=conn):
                self.create_index(keys, unique=True, _conn=conn)
            
            self._ensure_table_and_columns(row, conn)
            sa_table = self._get_sa_table(conn)
            values_to_update = {k: v for k, v in row.items() if k not in keys}
            
            stmt = sqlite.insert(sa_table).values(**row)
            stmt = stmt.on_conflict_do_update(index_elements=keys, set_=values_to_update)
            conn.execute(stmt)
            if self.database._tx is None:
                if hasattr(conn, 'commit'): conn.commit()
        finally:
            if not self.database._tx:
                conn.close()

    def delete(self, **filters):
        """Delete rows matching the filters."""
        conn = self.database._get_connection()
        try:
            sa_table = self._get_sa_table(conn)
            if sa_table is None: return 0

            stmt = sa_table.delete()
            if filters:
                clauses = [sa_table.c[k] == v for k, v in filters.items()]
                stmt = stmt.where(sqlalchemy.and_(*clauses))
            
            result = conn.execute(stmt)
            if self.database._tx is None:
                if hasattr(conn, 'commit'): conn.commit()
            return result.rowcount
        finally:
            if not self.database._tx:
                conn.close()

    def _build_select_query(self, conn, **filters):
        sa_table = self._get_sa_table(conn)
        if sa_table is None: return None
        
        stmt = sa_table.select()
        if filters:
            clauses = [sa_table.c[k] == v for k, v in filters.items()]
            stmt = stmt.where(sqlalchemy.and_(*clauses))
        return stmt

    def all(self):
        """Return an iterator for all rows in the table."""
        return self.find()

    def find(self, **filters):
        """Find rows matching the given filters."""
        conn = self.database._get_connection()
        try:
            stmt = self._build_select_query(conn, **filters)
            if stmt is None: return iter([])
            
            result = conn.execute(stmt)
            for row in result.mappings():
                yield dict(row)
        finally:
            if not self.database._tx:
                conn.close()

    def find_one(self, **filters):
        """Find a single row matching the filters."""
        conn = self.database._get_connection()
        try:
            stmt = self._build_select_query(conn, **filters)
            if stmt is None: return None
            
            result = conn.execute(stmt.limit(1))
            row = result.mappings().first()
            return dict(row) if row else None
        finally:
            if not self.database._tx:
                conn.close()

    def distinct(self, column, **filters):
        """Return distinct values for a column."""
        conn = self.database._get_connection()
        try:
            sa_table = self._get_sa_table(conn)
            if sa_table is None: return iter([])

            stmt = sqlalchemy.select(sa_table.c[column]).distinct()
            if filters:
                clauses = [sa_table.c[k] == v for k, v in filters.items()]
                stmt = stmt.where(sqlalchemy.and_(*clauses))
            
            result = conn.execute(stmt)
            for row in result:
                yield row[0]
        finally:
            if not self.database._tx:
                conn.close()

    def count(self, **filters):
        """Return the number of rows in the table."""
        conn = self.database._get_connection()
        try:
            sa_table = self._get_sa_table(conn)
            if sa_table is None: return 0

            stmt = sqlalchemy.select(sqlalchemy.func.count()).select_from(sa_table)
            if filters:
                clauses = [sa_table.c[k] == v for k, v in filters.items()]
                stmt = stmt.where(sqlalchemy.and_(*clauses))
            
            return conn.execute(stmt).scalar_one()
        finally:
            if not self.database._tx:
                conn.close()

    def create_index(self, columns, unique=False, _conn=None):
        """Create an index on one or more columns."""
        columns = [columns] if not isinstance(columns, (list, tuple)) else columns
        conn = _conn or self.database._get_connection()
        try:
            sa_table = self._get_sa_table(conn)
            if sa_table is None:
                raise RuntimeError("Table does not exist, cannot create index.")

            index_name = f"ix_{self.name}_{'_'.join(columns)}"
            index = Index(index_name, *[sa_table.c[col] for col in columns], unique=unique)
            index.create(bind=conn)
            if _conn is None and self.database._tx is None:
                if hasattr(conn, 'commit'): conn.commit()
        finally:
            if _conn is None and not self.database._tx:
                conn.close()

    def has_index(self, columns, _conn=None):
        """Check if an index exists on the given columns."""
        columns = [columns] if not isinstance(columns, (list, tuple)) else columns
        conn = _conn or self.database._get_connection()
        try:
            inspector = sqlalchemy.inspect(conn)
            if not inspector.has_table(self.name): return False
            
            indexes = inspector.get_indexes(self.name)
            for index in indexes:
                if index['column_names'] == columns:
                    return True
            return False
        finally:
            if _conn is None and not self.database._tx:
                conn.close()

    @property
    def columns(self):
        """Return a list of column names in the table."""
        conn = self.database._get_connection()
        try:
            inspector = sqlalchemy.inspect(conn)
            if not inspector.has_table(self.name): return []
            return [c['name'] for c in inspector.get_columns(self.name)]
        finally:
            if not self.database._tx:
                conn.close()

    def __len__(self):
        """Return the number of rows in the table."""
        return self.count()

    def __repr__(self):
        return f"<Table({self.name!r})>"