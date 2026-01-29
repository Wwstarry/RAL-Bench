import os
import time
import petl


def test_fromdicts_convert_select_sort_addfield():
    t = petl.fromdicts(
        [
            {"id": "2", "amount": "10"},
            {"id": "1", "amount": "2"},
            {"id": "3", "amount": "7"},
        ],
        header=["id", "amount"],
    )
    t2 = petl.convert(t, "amount", int)
    t3 = petl.selectgt(t2, "amount", 5)
    t4 = petl.addfield(t3, "double", lambda r: r[1] * 2)
    t5 = petl.sort(t4, "id")

    rows = list(t5)
    assert rows[0] == ("id", "amount", "double")
    assert rows[1:] == [("2", 10, 20), ("3", 7, 14)]


def test_select_predicate_rowdict_fallback():
    t = [
        ("id", "x"),
        ("a", "1"),
        ("b", "2"),
        ("c", "3"),
    ]
    out = list(petl.select(t, lambda rec: int(rec["x"]) >= 2))
    assert out == [("id", "x"), ("b", "2"), ("c", "3")]


def test_join_inner_and_header_key_dedup_and_one_to_many():
    left = petl.fromdicts(
        [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}],
        header=["id", "name"],
    )
    right = petl.fromdicts(
        [{"id": 1, "color": "red"}, {"id": 1, "color": "blue"}, {"id": 3, "color": "green"}],
        header=["id", "color"],
    )
    j = petl.join(left, right, key="id")
    rows = list(j)
    assert rows[0] == ("id", "name", "color")
    assert rows[1:] == [(1, "a", "red"), (1, "a", "blue")]


def test_csv_roundtrip(tmp_path):
    p = tmp_path / "x.csv"
    t = [
        ("id", "val"),
        ("1", "a"),
        ("2", "b"),
    ]
    petl.tocsv(t, str(p))
    r = petl.fromcsv(str(p))
    assert list(r) == [("id", "val"), ("1", "a"), ("2", "b")]


def test_streaming_select_does_not_preconsume_all():
    class CountingTable:
        def __init__(self, n):
            self.n = n
            self.count = 0

        def __iter__(self):
            yield ("i",)
            for i in range(self.n):
                self.count += 1
                yield (i,)

    src = CountingTable(1000000)
    out = petl.selectgt(src, "i", 10)

    it = iter(out)
    assert next(it) == ("i",)
    # consume only a few rows; upstream count should not approach full size
    for _ in range(5):
        next(it)
    assert src.count < 1000


def test_performance_sanity_bulk_pipeline(tmp_path):
    # coarse check: avoid egregious slowness for moderate size
    p = tmp_path / "bulk.csv"
    n = 20000
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write("id,x\n")
        for i in range(n):
            f.write(f"{i},{i%100}\n")

    t0 = time.time()
    t = petl.fromcsv(str(p))
    t = petl.convert(t, "x", int)
    t = petl.selectge(t, "x", 50)
    t = petl.addfield(t, "y", lambda r: r[1] + 1)
    # force evaluation
    rows = list(t)
    dt = time.time() - t0

    assert rows[0] == ("id", "x", "y")
    assert len(rows) > 1
    assert dt < 2.5