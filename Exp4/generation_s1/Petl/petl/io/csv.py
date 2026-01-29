from __future__ import annotations

import csv
from typing import Any, Iterable, Iterator, Sequence, Tuple


def fromcsv(path: str, encoding: str = "utf-8", dialect: str = "excel", **csv_kwargs):
    """
    Lazy CSV source. Each iteration re-opens the file.
    Yields tuples of strings (as returned by csv.reader).
    """

    class CsvView:
        def __iter__(self) -> Iterator[Tuple[str, ...]]:
            with open(path, "r", encoding=encoding, newline="") as f:
                reader = csv.reader(f, dialect=dialect, **csv_kwargs)
                for row in reader:
                    yield tuple(row)

    return CsvView()


def tocsv(
    table: Iterable[Sequence[Any]],
    path: str,
    encoding: str = "utf-8",
    dialect: str = "excel",
    write_header: bool = True,
    **csv_kwargs,
) -> None:
    """
    CSV sink. Iterates the table and writes rows.
    """
    it = iter(table)
    with open(path, "w", encoding=encoding, newline="") as f:
        writer = csv.writer(f, dialect=dialect, **csv_kwargs)
        try:
            header = next(it)
        except StopIteration:
            return

        if write_header:
            writer.writerow(list(header))

        for row in it:
            writer.writerow(list(row))