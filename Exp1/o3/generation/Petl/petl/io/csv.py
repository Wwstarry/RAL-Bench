"""
CSV input / output helpers
"""

import csv
from pathlib import Path

from .. import Table


def fromcsv(path, **csv_kwargs):
    """
    Lazily read a CSV file.

    Parameters
    ----------
    path : str or path-like
        File system path.
    csv_kwargs : dict
        Additional keyword arguments passed verbatim to ``csv.reader``.
    """

    def _factory():
        file_path = Path(path)

        # open the file afresh on each iteration to maintain laziness and
        # re-iterability
        with file_path.open(newline="", encoding=csv_kwargs.pop("encoding", "utf-8")) as fh:
            reader = csv.reader(fh, **csv_kwargs)
            for row in reader:
                yield tuple(row)

    return Table(_factory)


def tocsv(table, path, **csv_kwargs):
    """
    Materialise *table* to *path* as CSV.

    Parameters
    ----------
    table : Table or iterable
        Source data to write.
    path : str or path-like
        Output filename.
    csv_kwargs : dict
        Additional parameters forwarded to ``csv.writer``.
    """

    file_path = Path(path)
    with file_path.open("w", newline="", encoding=csv_kwargs.pop("encoding", "utf-8")) as fh:
        writer = csv.writer(fh, **csv_kwargs)
        for row in table:
            writer.writerow(row)