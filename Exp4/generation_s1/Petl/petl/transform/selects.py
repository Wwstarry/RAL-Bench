from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Iterator, Sequence, Tuple, Union

Field = Union[int, str]


def _as_tuple(row: Sequence[Any]) -> Tuple[Any, ...]:
    return row if isinstance(row, tuple) else tuple(row)


def _as_field_index(header: Sequence[Any], field: Field) -> int:
    if isinstance(field, int):
        if field < 0 or field >= len(header):
            raise IndexError(field)
        return field
    try:
        return list(header).index(field)
    except ValueError as e:
        raise KeyError(field) from e


def select(table: Iterable[Sequence[Any]], predicate: Callable):
    """
    Filter rows based on predicate.

    predicate is attempted as predicate(row); if that raises TypeError, it is
    attempted as predicate(rowdict).
    """

    class SelectView:
        def __iter__(self) -> Iterator[Tuple[Any, ...]]:
            it = iter(table)
            header = _as_tuple(next(it))
            yield header
            hdr_list = list(header)

            for r0 in it:
                row = _as_tuple(r0)
                try:
                    ok = predicate(row)
                except TypeError:
                    ok = predicate(dict(zip(hdr_list, row)))
                if ok:
                    yield row

    return SelectView()


def _cmp_safe(op: Callable[[Any, Any], bool], value: Any, threshold: Any) -> bool:
    if threshold is None:
        return False
    if value is None:
        return False
    if value == "":
        return False
    try:
        return op(value, threshold)
    except TypeError:
        return False


def selectge(table: Iterable[Sequence[Any]], field: Field, threshold: Any):
    class SelectGeView:
        def __iter__(self) -> Iterator[Tuple[Any, ...]]:
            it = iter(table)
            header = _as_tuple(next(it))
            idx = _as_field_index(header, field)
            yield header
            for r0 in it:
                row = _as_tuple(r0)
                v = row[idx] if idx < len(row) else None
                if _cmp_safe(lambda a, b: a >= b, v, threshold):
                    yield row

    return SelectGeView()


def selectgt(table: Iterable[Sequence[Any]], field: Field, threshold: Any):
    class SelectGtView:
        def __iter__(self) -> Iterator[Tuple[Any, ...]]:
            it = iter(table)
            header = _as_tuple(next(it))
            idx = _as_field_index(header, field)
            yield header
            for r0 in it:
                row = _as_tuple(r0)
                v = row[idx] if idx < len(row) else None
                if _cmp_safe(lambda a, b: a > b, v, threshold):
                    yield row

    return SelectGtView()