from __future__ import annotations

from typing import Any, Iterable, Iterator, List, Sequence, Tuple, Union

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


def sort(table: Iterable[Sequence[Any]], field: Field, reverse: bool = False):
    """
    Sort rows by a field. This is a blocking operation (materializes all data rows).
    """

    class SortView:
        def __iter__(self) -> Iterator[Tuple[Any, ...]]:
            it = iter(table)
            header = _as_tuple(next(it))
            idx = _as_field_index(header, field)
            rows: List[Tuple[Any, ...]] = [_as_tuple(r) for r in it]

            def keyfunc(r: Tuple[Any, ...]):
                v = r[idx] if idx < len(r) else None
                return (v is None, v)

            rows.sort(key=keyfunc, reverse=reverse)
            yield header
            for r in rows:
                yield r

    return SortView()