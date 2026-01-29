from __future__ import annotations

import typing as t

from ._compat import is_optional, optional_inner, json_dumps
from .exceptions import UnmappedInstanceError
from .fields import FieldInfo, Undefined
from .orm import Column, MetaData, RelationshipInfo, Table


class ModelField:
    def __init__(self, name: str, annotation: t.Any, field_info: FieldInfo):
        self.name = name
        self.annotation = annotation
        self.field_info = field_info
        self.required = field_info.default is Undefined and field_info.default_factory is None

    def get_default(self) -> t.Any:
        return self.field_info.get_default()


class SQLModelMeta(type):
    def __new__(mcls, name: str, bases: tuple[type, ...], namespace: dict, **kwargs: t.Any):
        table_flag = bool(kwargs.pop("table", False))
        cls = super().__new__(mcls, name, bases, dict(namespace))

        if name == "SQLModel":
            return cls

        # inherit/merge annotations
        annotations: dict[str, t.Any] = {}
        for b in reversed(bases):
            annotations.update(getattr(b, "__annotations__", {}) or {})
        annotations.update(namespace.get("__annotations__", {}) or {})

        fields: dict[str, ModelField] = {}
        relationships: dict[str, RelationshipInfo] = {}

        for fname, ann in annotations.items():
            val = namespace.get(fname, getattr(cls, fname, Undefined))
            if isinstance(val, RelationshipInfo):
                relationships[fname] = val
                continue

            if isinstance(val, FieldInfo):
                finfo = val
            else:
                finfo = FieldInfo(default=val)

            fields[fname] = ModelField(fname, ann, finfo)

        cls.__sqlmodel_fields__ = fields
        cls.__fields__ = fields  # pydantic v1-ish
        cls.model_fields = fields  # pydantic v2-ish
        cls.__sqlmodel_relationships__ = relationships

        if table_flag:
            # tablename
            if not hasattr(cls, "__tablename__"):
                cls.__tablename__ = name.lower()

            columns: dict[str, Column] = {}
            for fname, f in fields.items():
                ann = f.annotation
                base_type = optional_inner(ann)
                nullable = f.field_info.nullable
                if nullable is None:
                    nullable = bool(is_optional(ann) or f.field_info.default is None)

                default = f.get_default()
                if default is Undefined:
                    default = None

                col = Column(
                    model_cls=cls,
                    name=fname,
                    python_type=base_type,
                    primary_key=f.field_info.primary_key,
                    nullable=nullable,
                    default=default,
                    index=f.field_info.index,
                    unique=f.field_info.unique,
                )
                columns[fname] = col

            cls.__table__ = Table(cls.__tablename__, cls, columns)

            # attach Column descriptors to class (to build expressions)
            for fname, col in columns.items():
                setattr(cls, fname, col)

            # register in global metadata
            SQLModel.metadata.tables[cls.__tablename__] = cls.__table__

        return cls


class SQLModel(metaclass=SQLModelMeta):
    metadata = MetaData()

    def __init__(self, **data: t.Any):
        cls = self.__class__
        fields: dict[str, ModelField] = getattr(cls, "__sqlmodel_fields__", {})

        for name, mf in fields.items():
            if name in data:
                value = data[name]
            else:
                dv = mf.get_default()
                if dv is Undefined:
                    value = None
                else:
                    value = dv

            value = self._coerce_value(mf.annotation, value)
            object.__setattr__(self, name, value)

        extra = {k: v for k, v in data.items() if k not in fields}
        for k, v in extra.items():
            object.__setattr__(self, k, v)

    @classmethod
    def model_validate(cls, obj: t.Any) -> "SQLModel":
        if isinstance(obj, cls):
            return obj
        if isinstance(obj, dict):
            return cls(**obj)
        raise TypeError("model_validate expects a dict or instance")

    @classmethod
    def parse_obj(cls, obj: t.Any) -> "SQLModel":
        return cls.model_validate(obj)

    def dict(self, *, exclude_none: bool = False, **kwargs: t.Any) -> dict:
        cls = self.__class__
        fields: dict[str, ModelField] = getattr(cls, "__sqlmodel_fields__", {})
        out = {}
        for name in fields.keys():
            val = getattr(self, name, None)
            if exclude_none and val is None:
                continue
            out[name] = val
        return out

    def model_dump(self, **kwargs: t.Any) -> dict:
        return self.dict(**kwargs)

    def json(self, **kwargs: t.Any) -> str:
        data = self.dict(**{k: v for k, v in kwargs.items() if k in {"exclude_none"}})
        json_kwargs = {k: v for k, v in kwargs.items() if k not in {"exclude_none"}}
        return json_dumps(data, **json_kwargs)

    def model_dump_json(self, **kwargs: t.Any) -> str:
        return self.json(**kwargs)

    def __repr__(self) -> str:
        cls = self.__class__
        fields: dict[str, ModelField] = getattr(cls, "__sqlmodel_fields__", {})
        parts = []
        for name in fields.keys():
            parts.append(f"{name}={getattr(self, name, None)!r}")
        return f"{cls.__name__}({', '.join(parts)})"

    @property
    def __table__(self) -> Table:  # type: ignore[override]
        t_ = getattr(self.__class__, "__table__", None)
        if t_ is None:
            raise UnmappedInstanceError("Instance is not mapped as a table model")
        return t_

    @staticmethod
    def _coerce_value(tp: t.Any, value: t.Any) -> t.Any:
        if value is None:
            return None
        base = optional_inner(tp)

        origin = t.get_origin(base)
        if origin is list:
            (inner,) = t.get_args(base) or (t.Any,)
            if isinstance(value, list):
                return [SQLModel._coerce_value(inner, v) for v in value]
            return list(value)

        if base in (int, float, str, bool):
            try:
                return base(value)
            except Exception:
                return value
        return value