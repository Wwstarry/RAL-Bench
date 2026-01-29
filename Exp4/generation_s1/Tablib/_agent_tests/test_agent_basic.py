import json
import pytest

import tablib


def test_dataset_construct_shape_and_access():
    ds = tablib.Dataset([1, 2], [3, 4], headers=["a", "b"])
    assert ds.headers == ["a", "b"]
    assert ds.height == 2
    assert ds.width == 2

    assert ds[0:1] == [(1, 2)]
    assert ds["a"] == [1, 3]
    assert ds["b"] == [2, 4]
    with pytest.raises(KeyError):
        _ = ds["missing"]


def test_dataset_append_and_slice_order():
    ds = tablib.Dataset(headers=["x", "y"])
    ds.append([10, 20])
    ds.append([11, 21])
    ds.append([12, 22])
    assert ds.height == 3
    assert ds.width == 2
    assert ds[1:3] == [(11, 21), (12, 22)]


def test_append_col_existing_rows_and_mismatch():
    ds = tablib.Dataset([1, 2], [3, 4], headers=["a", "b"])
    ds.append_col([9, 8], header="c")
    assert ds.headers == ["a", "b", "c"]
    assert ds.width == 3
    assert ds.height == 2
    assert ds["c"] == [9, 8]
    assert ds.dict == [{"a": 1, "b": 2, "c": 9}, {"a": 3, "b": 4, "c": 8}]

    with pytest.raises(ValueError):
        ds.append_col([1], header="bad")


def test_append_col_into_empty_dataset_creates_rows():
    ds = tablib.Dataset(headers=["a"])
    # no rows yet; append col creates rows
    ds.append_col([1, 2, 3], header="b")
    assert ds.height == 3
    assert ds.width == 2
    assert ds.headers == ["a", "b"]
    # 'a' column missing values are None
    assert ds["a"] == [None, None, None]
    assert ds["b"] == [1, 2, 3]


def test_csv_roundtrip_preserves_shape_and_order():
    ds = tablib.Dataset([90, 80], [70, 60], headers=["m", "n"])
    csv_text = ds.csv
    assert csv_text.splitlines()[0] == "m,n"

    ds2 = tablib.Dataset()
    ds2.csv = csv_text
    assert ds2.headers == ["m", "n"]
    assert ds2.height == 2
    assert ds2.width == 2
    # Imported as strings from CSV
    assert ds2.dict == [{"m": "90", "n": "80"}, {"m": "70", "n": "60"}]


def test_json_roundtrip_dataset_and_list_of_dicts_import():
    ds = tablib.Dataset([1, None], [3, 4], headers=["a", "b"], title="T")
    j = ds.json
    obj = json.loads(j)
    assert obj["title"] == "T"
    assert obj["headers"] == ["a", "b"]
    assert obj["data"][0] == [1, None]

    ds2 = tablib.Dataset()
    ds2.json = j
    assert ds2.title == "T"
    assert ds2.headers == ["a", "b"]
    assert ds2.dict == [{"a": 1, "b": None}, {"a": 3, "b": 4}]

    # list-of-dicts fallback
    ds3 = tablib.Dataset()
    ds3.json = json.dumps([{"x": 1, "y": 2}, {"x": 3, "y": 4}], separators=(",", ":"))
    assert ds3.headers == ["x", "y"]
    assert ds3.dict == [{"x": 1, "y": 2}, {"x": 3, "y": 4}]


def test_databook_json_preserves_sheets_titles_headers_and_rows():
    s1 = tablib.Dataset([1, 2], [3, 4], headers=["a", "b"], title="Sheet1")
    s2 = tablib.Dataset(["x"], ["y"], headers=["col"], title="Sheet2")
    book = tablib.Databook([s1, s2])

    assert book.size == 2
    assert [s.title for s in book.sheets()] == ["Sheet1", "Sheet2"]
    assert [s.title for s in list(book)] == ["Sheet1", "Sheet2"]

    j = book.export("json")
    book2 = tablib.Databook([])
    book2.json = j

    assert book2.size == 2
    sheets = book2.sheets()
    assert sheets[0].title == "Sheet1"
    assert sheets[0].headers == ["a", "b"]
    assert sheets[0].dict == [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    assert sheets[1].title == "Sheet2"
    assert sheets[1].headers == ["col"]
    assert sheets[1].dict == [{"col": "x"}, {"col": "y"}]