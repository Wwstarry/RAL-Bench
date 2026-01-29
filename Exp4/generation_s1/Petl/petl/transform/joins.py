from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Sequence, Tuple, Union

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


def join(left: Iterable[Sequence[Any]], right: Iterable[Sequence[Any]], key: Field = "id"):
    """
    Inner join on a key (field name or index). Right side is indexed in memory.
    """

    class JoinView:
        def __iter__(self) -> Iterator[Tuple[Any, ...]]:
            # index right
            it_r = iter(right)
            r_header = _as_tuple(next(it_r))
            r_key_idx = _as_field_index(r_header, key)
            r_rows_by_key: Dict[Any, List[Tuple[Any, ...]]] = {}
            for r0 in it_r:
                r = _as_tuple(r0)
                k = r[r_key_idx] if r_key_idx < len(r) else None
                r_rows_by_key.setdefault(k, []).append(r)

            # iterate left and produce
            it_l = iter(left)
            l_header = _as_tuple(next(it_l))
            l_key_idx = _as_field_index(l_header, key)

            # Build output header: left header + right fields excluding join key if same name exists
            l_fields = list(l_header)
            r_fields = list(r_header)

            r_out_indices: List[int] = []
            out_r_names: List[Any] = []
            for i, name in enumerate(r_fields):
                if i == r_key_idx:
                    # exclude right key if left already has that field name
                    if (isinstance(key, str) and key in l_fields) or (i == r_key_idx and r_fields[r_key_idx] in l_fields):
                        continue
                out_name = name
                if out_name in l_fields:
                    out_name = f"{out_name}_right"
                out_r_names.append(out_name)
                r_out_indices.append(i)

            out_header = tuple(l_fields + out_r_names)
            yield out_header

            for l0 in it_l:
                lrow = _as_tuple(l0)
                lk = lrow[l_key_idx] if l_key_idx < len(lrow) else None
                matches = r_rows_by_key.get(lk)
                if not matches:
                    continue
                for rrow in matches:
                    extra = tuple(rrow[i] if i < len(rrow) else None for i in r_out_indices)
                    yield lrow + extra

    return JoinView()