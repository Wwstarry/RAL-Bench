from __future__ import annotations

import typing as t


class Engine:
    def __init__(self, url: str, *, echo: bool = False, connect_args: t.Optional[dict] = None, **kwargs: t.Any):
        self.url = url
        self.echo = echo
        self.connect_args = connect_args or {}
        self.kwargs = dict(kwargs)
        self._db: dict[str, dict[str, t.Any]] = {}  # table_name -> {"rows": [dict], "ai": int, "table": Table}

    def _ensure_table(self, table: "Table") -> None:
        from .orm import Table  # avoid cycle

        if not isinstance(table, Table):
            raise TypeError("table must be a Table")
        if table.name not in self._db:
            self._db[table.name] = {"rows": [], "ai": 1, "table": table}

    def _drop_all(self) -> None:
        self._db.clear()


def create_engine(
    url: str,
    *,
    echo: bool = False,
    connect_args: t.Optional[dict] = None,
    **kwargs: t.Any,
) -> Engine:
    return Engine(url, echo=echo, connect_args=connect_args, **kwargs)