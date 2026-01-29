def select(table, predicate):
    """
    Select rows where predicate(row) is truthy.

    predicate may accept either:
      - row tuple, or
      - dict mapping field -> value (rowdict).
    """

    class _SelectTable:
        def __init__(self, src, pred):
            self._src = src
            self._pred = pred

        def __iter__(self):
            it = iter(self._src)
            header = next(it)
            header = tuple(header)
            yield header

            for row in it:
                row = tuple(row)
                rowdict = dict(zip(header, row))
                try:
                    keep = self._pred(rowdict)
                except TypeError:
                    keep = self._pred(row)
                if keep:
                    yield row

    return _SelectTable(table, predicate)


def _select_compare(table, field, threshold, op):
    class _SelectCompareTable:
        def __init__(self, src, fld, thr, op_):
            self._src = src
            self._field = fld
            self._threshold = thr
            self._op = op_

        def __iter__(self):
            it = iter(self._src)
            header = next(it)
            header = tuple(header)
            yield header

            if isinstance(self._field, int):
                idx = self._field
            else:
                try:
                    idx = header.index(self._field)
                except ValueError:
                    raise KeyError(self._field)

            thr = self._threshold
            op_ = self._op
            for row in it:
                row = tuple(row)
                if op_(row[idx], thr):
                    yield row

    return _SelectCompareTable(table, field, threshold, op)


def selectge(table, field, threshold):
    return _select_compare(table, field, threshold, lambda a, b: a >= b)


def selectgt(table, field, threshold):
    return _select_compare(table, field, threshold, lambda a, b: a > b)