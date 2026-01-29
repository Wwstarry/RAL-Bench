from __future__ import annotations

import typing as t

from .exceptions import TableNotCreatedError, UnmappedInstanceError
from .orm import Column, Condition
from .sql import Result, Row, Select


class Session:
    def __init__(self, engine: "Engine", **kwargs: t.Any):
        from .engine import Engine

        if not isinstance(engine, Engine):
            raise TypeError("Session requires an Engine")
        self.engine = engine
        self.kwargs = dict(kwargs)
        self._new: list[t.Any] = []
        self._closed = False

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        self._closed = True

    def add(self, instance: t.Any) -> None:
        table = getattr(instance.__class__, "__table__", None)
        if table is None:
            raise UnmappedInstanceError("Can only add SQLModel table models")
        self._new.append(instance)

    def add_all(self, instances: list[t.Any]) -> None:
        for inst in instances:
            self.add(inst)

    def commit(self) -> None:
        # Insert-only minimal UoW
        for inst in list(self._new):
            table = inst.__class__.__table__
            tname = table.name
            if tname not in self.engine._db:
                raise TableNotCreatedError(f"Table '{tname}' is not created. Call SQLModel.metadata.create_all(engine).")

            bucket = self.engine._db[tname]
            row = {}
            for col_name, col in table.columns.items():
                val = getattr(inst, col_name, None)
                if col.primary_key and (val is None):
                    val = bucket["ai"]
                    bucket["ai"] += 1
                    setattr(inst, col_name, val)
                row[col_name] = val
            bucket["rows"].append(row)
            self._new.remove(inst)

    def rollback(self) -> None:
        self._new.clear()

    def refresh(self, instance: t.Any) -> None:
        table = getattr(instance.__class__, "__table__", None)
        if table is None:
            raise UnmappedInstanceError("Can only refresh SQLModel table models")

        pkcol = table.primary_key
        if pkcol is None:
            return
        pk = getattr(instance, pkcol.name, None)
        if pk is None:
            return
        found = self._find_row(table, pk)
        if found is None:
            return
        for k, v in found.items():
            setattr(instance, k, v)

    def get(self, model_cls: type, pk: t.Any) -> t.Any:
        table = getattr(model_cls, "__table__", None)
        if table is None:
            raise UnmappedInstanceError("Can only get() SQLModel table models")
        if table.name not in self.engine._db:
            raise TableNotCreatedError(f"Table '{table.name}' is not created. Call SQLModel.metadata.create_all(engine).")
        row = self._find_row(table, pk)
        if row is None:
            return None
        return self._row_to_model(model_cls, row)

    def exec(self, statement: Select) -> Result:
        return self.execute(statement)

    def execute(self, statement: Select) -> Result:
        if not isinstance(statement, Select):
            raise TypeError("Session.execute expects a Select statement")

        entities = statement.entities

        # Determine "FROM" model (first entity that is a model class with __table__)
        model_cls = None
        for ent in entities:
            if isinstance(ent, type) and getattr(ent, "__table__", None) is not None:
                model_cls = ent
                break
        if model_cls is None:
            # support select(Model.col, ...) where Model.col is Column
            for ent in entities:
                if isinstance(ent, Column):
                    model_cls = ent.model_cls
                    break

        if model_cls is None:
            raise TypeError("Could not determine selectable model")

        table = model_cls.__table__
        if table.name not in self.engine._db:
            raise TableNotCreatedError(f"Table '{table.name}' is not created. Call SQLModel.metadata.create_all(engine).")

        rows = list(self.engine._db[table.name]["rows"])

        # where filters (AND semantics)
        for cond in statement._where:
            rows = [r for r in rows if cond.eval(r)]

        # order_by (only basic column ordering)
        for ob in reversed(statement._order_by):
            if isinstance(ob, Column):
                rows.sort(key=lambda rr: rr.get(ob.name))
            else:
                # unknown order_by; ignore
                pass

        # offset/limit
        if statement._offset:
            rows = rows[statement._offset :]
        if statement._limit is not None:
            rows = rows[: statement._limit]

        # shape result
        if len(entities) == 1 and entities[0] is model_cls:
            models = [self._row_to_model(model_cls, r) for r in rows]
            return Result(models, scalar_index=None)

        out_rows: list[Row] = []
        for r in rows:
            values = []
            for ent in entities:
                if ent is model_cls:
                    values.append(self._row_to_model(model_cls, r))
                elif isinstance(ent, Column):
                    values.append(r.get(ent.name))
                else:
                    # fallback: if a class attribute Column was passed, it will be Column
                    values.append(ent)
            out_rows.append(Row(tuple(values)))

        scalar_index = 0 if len(entities) == 1 else None
        return Result(out_rows, scalar_index=scalar_index)

    def _find_row(self, table: "Table", pk: t.Any) -> t.Optional[dict]:
        pkcol = table.primary_key
        if pkcol is None:
            return None
        for r in self.engine._db[table.name]["rows"]:
            if r.get(pkcol.name) == pk:
                return r
        return None

    def _row_to_model(self, model_cls: type, row: dict) -> t.Any:
        # create instance without calling __init__ (to avoid type coercion issues)
        obj = model_cls.__new__(model_cls)
        fields = getattr(model_cls, "__sqlmodel_fields__", {})
        for name in fields.keys():
            setattr(obj, name, row.get(name))
        return obj