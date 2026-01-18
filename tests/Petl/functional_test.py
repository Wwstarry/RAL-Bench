from __future__ import annotations

import csv
import os
import sys
import types
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import pytest

# ---------------------------------------------------------------------------
# Repo root resolution (RACB-compatible + local fallback)
#
# RACB requirement (preferred): use RACB_REPO_ROOT and support both layouts:
#   - <repo_root>/petl/__init__.py
#   - <repo_root>/src/petl/__init__.py
#
# Local fallback (no absolute path hardcode): keep original eval layout:
#   <eval_root>/repositories/Petl  OR  <eval_root>/generation/Petl
# ---------------------------------------------------------------------------

PACKAGE_NAME = "petl"

_racb_root = os.environ.get("RACB_REPO_ROOT", "").strip()
if _racb_root:
    REPO_ROOT = Path(_racb_root).resolve()
else:
    ROOT = Path(__file__).resolve().parents[2]
    target = os.getenv("PETL_TARGET", "reference").lower()
    if target == "reference":
        REPO_ROOT = ROOT / "repositories" / "Petl"
    elif target == "generation":
        REPO_ROOT = ROOT / "generation" / "Petl"
    else:
        pytest.skip(
            "Unsupported PETL_TARGET value: {}".format(target),
            allow_module_level=True,
        )

if not REPO_ROOT.exists():
    pytest.skip(
        "Repository root does not exist: {}".format(REPO_ROOT),
        allow_module_level=True,
    )

src_pkg_init = REPO_ROOT / "src" / PACKAGE_NAME / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE_NAME / "__init__.py"

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Could not find '{}' package under repo root. Expected {} or {}.".format(
            PACKAGE_NAME, src_pkg_init, root_pkg_init
        ),
        allow_module_level=True,
    )

# Some petl versions expect a generated petl.version module which is not present
# in a plain source checkout. Provide a lightweight stub so that imports succeed.
version_module_path = (REPO_ROOT / "src" / "petl" / "version.py") if src_pkg_init.exists() else (REPO_ROOT / "petl" / "version.py")
if not version_module_path.exists():
    stub = types.ModuleType("petl.version")
    stub.version = "0.0.0"
    sys.modules["petl.version"] = stub

try:
    import petl  # type: ignore[import]  # noqa: E402
except Exception as exc:
    pytest.skip(
        "Failed to import petl from {}: {}".format(REPO_ROOT, exc),
        allow_module_level=True,
    )


def _table_to_list_of_dicts(table: Iterable[Iterable[Any]]) -> List[Dict[str, Any]]:
    """Convert a petl table into a list of dictionaries using the header row."""
    iterator = iter(table)
    try:
        header = tuple(next(iterator))
    except StopIteration:
        return []
    rows: List[Dict[str, Any]] = []
    for row in iterator:
        rows.append(dict(zip(header, row)))
    return rows


def _normalize_dicts(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Normalize values in a list of dicts to strings for robust comparisons."""
    normalized: List[Dict[str, str]] = []
    for row in rows:
        normalized.append({k: str(v) for k, v in row.items()})
    return normalized


def _require_attr(name: str) -> None:
    """Skip the current test if petl does not expose the named attribute/function."""
    if not hasattr(petl, name):
        pytest.skip("petl.{} is not available in this implementation".format(name))


def _read_csv_rows(path: Path) -> List[List[str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def _write_csv_rows(path: Path, rows: Sequence[Sequence[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for r in rows:
            writer.writerow(list(r))


# ---------------------------------------------------------------------------
# Core ETL tests (happy path only)
# ---------------------------------------------------------------------------

def test_fromcsv_convert_select_sort_and_tocsv_roundtrip(tmp_path: Path) -> None:
    """Exercise a CSV-based ETL pipeline using fromcsv/convert/select/sort/tocsv."""
    source_csv = tmp_path / "people.csv"
    output_csv = tmp_path / "filtered_sorted.csv"

    rows = [
        ("name", "age", "city"),
        ("Alice", "25", "London"),
        ("Bob", "40", "Paris"),
        ("Carol", "35", "Berlin"),
        ("Dave", "18", "Rome"),
    ]
    _write_csv_rows(source_csv, rows)

    table = petl.fromcsv(str(source_csv))

    table = petl.convert(table, "age", int)
    table = petl.selectge(table, "age", 30)
    table = petl.sort(table, "age")

    petl.tocsv(table, str(output_csv))
    assert output_csv.exists()

    written_rows = _read_csv_rows(output_csv)

    assert written_rows[0] == ["name", "age", "city"]
    data_rows = written_rows[1:]
    ages = [int(r[1]) for r in data_rows]
    names = [r[0] for r in data_rows]
    assert ages == sorted(ages)
    assert set(names) == {"Bob", "Carol"}


def test_fromdicts_addfield_and_select() -> None:
    """Validate fromdicts, addfield, and select with a small in-memory table."""
    records = [
        {"id": 1, "value": 10},
        {"id": 2, "value": 20},
        {"id": 3, "value": 30},
        {"id": 4, "value": 40},
    ]
    table = petl.fromdicts(records, header=["id", "value"])

    table = petl.addfield(table, "double", lambda rec: int(rec["value"]) * 2)
    table = petl.select(table, lambda rec: int(rec["double"]) >= 60)

    result = _table_to_list_of_dicts(table)
    ids = sorted(int(row["id"]) for row in result)
    doubles = sorted(int(row["double"]) for row in result)

    assert ids == [3, 4]
    assert doubles == [60, 80]


def test_join_two_tables_fromdicts() -> None:
    """Check that an inner join between two small tables behaves as expected."""
    customers = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Carol"},
    ]
    orders = [
        {"id": 1, "amount": 100},
        {"id": 1, "amount": 50},
        {"id": 2, "amount": 200},
    ]

    customers_tbl = petl.fromdicts(customers, header=["id", "name"])
    orders_tbl = petl.fromdicts(orders, header=["id", "amount"])

    joined = petl.join(customers_tbl, orders_tbl, key="id")
    result = _table_to_list_of_dicts(joined)

    assert len(result) == 3
    for row in result:
        assert "id" in row
        assert "name" in row
        assert "amount" in row

    names_for_id1 = {row["name"] for row in result if int(row["id"]) == 1}
    assert names_for_id1 == {"Alice"}


# ---------------------------------------------------------------------------
# Additional functional coverage (>= 10 test_* functions total)
# ---------------------------------------------------------------------------

def test_cut_and_rename_columns() -> None:
    """Use cut/rename to reshape a table and verify header + data."""
    _require_attr("cut")
    _require_attr("rename")

    records = [
        {"id": 1, "value": 10, "city": "London"},
        {"id": 2, "value": 20, "city": "Paris"},
    ]
    table = petl.fromdicts(records, header=["id", "value", "city"])

    cut_tbl = petl.cut(table, "id", "value")
    renamed = petl.rename(cut_tbl, "value", "val")

    rows = list(renamed)
    assert rows[0] == ("id", "val")
    assert rows[1] == (1, 10)
    assert rows[2] == (2, 20)


def test_selecteq_and_selectin_filters() -> None:
    """Filter rows using selecteq/selectin and verify the resulting ids."""
    _require_attr("selecteq")
    _require_attr("selectin")

    records = [
        {"id": 1, "city": "London"},
        {"id": 2, "city": "Paris"},
        {"id": 3, "city": "Berlin"},
        {"id": 4, "city": "Paris"},
    ]
    table = petl.fromdicts(records, header=["id", "city"])

    paris = petl.selecteq(table, "city", "Paris")
    paris_rows = _table_to_list_of_dicts(paris)
    assert sorted(int(r["id"]) for r in paris_rows) == [2, 4]

    subset = petl.selectin(table, "city", {"London", "Berlin"})
    subset_rows = _table_to_list_of_dicts(subset)
    assert sorted(int(r["id"]) for r in subset_rows) == [1, 3]


def test_convert_with_lambda_and_values_preserved() -> None:
    """Convert a column with a lambda and verify new typed values."""
    records = [
        {"id": "1", "amount": "100"},
        {"id": "2", "amount": "250"},
    ]
    table = petl.fromdicts(records, header=["id", "amount"])

    converted = petl.convert(table, "amount", lambda v: int(v) + 1)
    rows = _table_to_list_of_dicts(converted)

    assert [int(r["amount"]) for r in rows] == [101, 251]
    assert [str(r["id"]) for r in rows] == ["1", "2"]


def test_sort_descending_orders_values() -> None:
    """Sort descending by a numeric field."""
    _require_attr("sort")

    records = [
        {"name": "A", "score": 10},
        {"name": "B", "score": 30},
        {"name": "C", "score": 20},
    ]
    table = petl.fromdicts(records, header=["name", "score"])

    # petl.sort supports reverse=True in typical implementations.
    sorted_tbl = petl.sort(table, "score", reverse=True)
    rows = _table_to_list_of_dicts(sorted_tbl)

    scores = [int(r["score"]) for r in rows]
    names = [r["name"] for r in rows]
    assert scores == [30, 20, 10]
    assert names == ["B", "C", "A"]


def test_leftjoin_keeps_all_left_rows(tmp_path: Path) -> None:
    """Left join should keep all rows from the left table."""
    _require_attr("leftjoin")

    left = petl.fromdicts(
        [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}, {"id": 3, "name": "Carol"}],
        header=["id", "name"],
    )
    right = petl.fromdicts(
        [{"id": 1, "tier": "gold"}, {"id": 3, "tier": "silver"}],
        header=["id", "tier"],
    )

    joined = petl.leftjoin(left, right, key="id")
    rows = _table_to_list_of_dicts(joined)
    assert len(rows) == 3

    # Verify id->tier mapping where available; missing tiers remain blank/None depending on impl.
    by_id = {int(r["id"]): r for r in rows}
    assert by_id[1]["name"] == "Alice"
    assert str(by_id[1].get("tier")) in ("gold", "Gold", "gold ")

    assert by_id[2]["name"] == "Bob"
    assert "tier" in by_id[2]  # present as a column, even if empty

    assert by_id[3]["name"] == "Carol"
    assert str(by_id[3].get("tier")) in ("silver", "Silver", "silver ")


def test_tocsv_then_fromcsv_preserves_data(tmp_path: Path) -> None:
    """Write a table to CSV and read it back, verifying header and row content."""
    src = tmp_path / "roundtrip.csv"

    table = petl.fromdicts(
        [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}],
        header=["a", "b"],
    )
    petl.tocsv(table, str(src))
    assert src.exists()

    table2 = petl.fromcsv(str(src))
    rows = list(table2)

    assert rows[0] == ("a", "b")
    assert rows[1] == ("1", "x") or rows[1] == (1, "x")
    assert rows[2] == ("2", "y") or rows[2] == (2, "y")


def test_stack_concatenates_tables() -> None:
    """Stack two compatible tables and verify combined row count."""
    _require_attr("stack")

    t1 = petl.fromdicts([{"id": 1, "v": "a"}, {"id": 2, "v": "b"}], header=["id", "v"])
    t2 = petl.fromdicts([{"id": 3, "v": "c"}], header=["id", "v"])

    stacked = petl.stack(t1, t2)
    rows = _table_to_list_of_dicts(stacked)

    assert len(rows) == 3
    assert [int(r["id"]) for r in rows] == [1, 2, 3]
    assert [r["v"] for r in rows] == ["a", "b", "c"]


def test_distinct_removes_duplicate_rows() -> None:
    """Use distinct to drop duplicate rows in a table."""
    _require_attr("distinct")

    table = petl.fromdicts(
        [{"id": 1, "v": "x"}, {"id": 1, "v": "x"}, {"id": 2, "v": "y"}],
        header=["id", "v"],
    )
    distinct_tbl = petl.distinct(table)
    rows = _table_to_list_of_dicts(distinct_tbl)

    # Expect two unique data rows.
    normalized = _normalize_dicts(rows)
    assert {"id": "1", "v": "x"} in normalized
    assert {"id": "2", "v": "y"} in normalized
    assert len(normalized) == 2


def test_recordlookup_returns_expected_fields() -> None:
    """Create a record lookup and verify retrieving a row by key."""
    _require_attr("recordlookup")

    table = petl.fromdicts(
        [{"id": 10, "name": "alpha"}, {"id": 20, "name": "beta"}],
        header=["id", "name"],
    )
    lookup = petl.recordlookup(table, key="id")

    rec = lookup[20]
    # recordlookup returns a dict-like record in typical implementations.
    assert str(rec["name"]) == "beta"
    assert int(rec["id"]) == 20
