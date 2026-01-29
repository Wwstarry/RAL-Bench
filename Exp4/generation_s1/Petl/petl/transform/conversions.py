from __future__ import annotations

from typing import Any, Callable, Iterable, Iterator, Sequence, Tuple, Union

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


def convert(
    table: Iterable[Sequence[Any]],
    field: Field,
    func: Callable[[Any], Any],
    failonerror: bool = False,
    default: Any = None,
):
    """
    Convert values in a field/column using func(value), streaming rows.

    If failonerror is False and func raises, uses `default` if provided (default is None);
    otherwise keeps the original value.
    """

    class ConvertView:
        def __iter__(self) -> Iterator[Tuple[Any, ...]]:
            it = iter(table)
            header = _as_tuple(next(it))
            idx = _as_field_index(header, field)
            yield header

            for row0 in it:
                row = _as_tuple(row0)
                old = row[idx] if idx < len(row) else None
                try:
                    new = func(old)
                except Exception:
                    if failonerror:
                        raise
                    if default is not None:
                        new = default
                    else:
                        new = old
                if idx >= len(row):
                    # pad (unlikely in tests)
                    padded = list(row) + [None] * (idx + 1 - len(row))
                    padded[idx] = new
                    yield tuple(padded)
                else:
                    yield row[:idx] + (new,) + row[idx + 1 :]

    return ConvertView()