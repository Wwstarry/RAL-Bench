from __future__ import annotations

import typing as t

Undefined = object()


class FieldInfo:
    __slots__ = (
        "default",
        "default_factory",
        "primary_key",
        "foreign_key",
        "nullable",
        "index",
        "unique",
        "max_length",
        "sa_column",
        "sa_column_kwargs",
        "description",
        "extra",
    )

    def __init__(
        self,
        default: t.Any = Undefined,
        *,
        default_factory: t.Optional[t.Callable[[], t.Any]] = None,
        primary_key: bool = False,
        foreign_key: t.Optional[str] = None,
        nullable: t.Optional[bool] = None,
        index: bool = False,
        unique: bool = False,
        max_length: t.Optional[int] = None,
        sa_column: t.Any = None,
        sa_column_kwargs: t.Optional[dict] = None,
        description: t.Optional[str] = None,
        **extra: t.Any,
    ):
        self.default = default
        self.default_factory = default_factory
        self.primary_key = bool(primary_key)
        self.foreign_key = foreign_key
        self.nullable = nullable
        self.index = bool(index)
        self.unique = bool(unique)
        self.max_length = max_length
        self.sa_column = sa_column
        self.sa_column_kwargs = sa_column_kwargs or None
        self.description = description
        self.extra = dict(extra)

    def get_default(self) -> t.Any:
        if self.default_factory is not None:
            return self.default_factory()
        if self.default is Undefined:
            return Undefined
        return self.default


def Field(
    default: t.Any = Undefined,
    *,
    default_factory: t.Optional[t.Callable[[], t.Any]] = None,
    primary_key: bool = False,
    foreign_key: t.Optional[str] = None,
    nullable: t.Optional[bool] = None,
    index: bool = False,
    unique: bool = False,
    max_length: t.Optional[int] = None,
    sa_column: t.Any = None,
    sa_column_kwargs: t.Optional[dict] = None,
    description: t.Optional[str] = None,
    **extra: t.Any,
) -> t.Any:
    return FieldInfo(
        default,
        default_factory=default_factory,
        primary_key=primary_key,
        foreign_key=foreign_key,
        nullable=nullable,
        index=index,
        unique=unique,
        max_length=max_length,
        sa_column=sa_column,
        sa_column_kwargs=sa_column_kwargs,
        description=description,
        **extra,
    )