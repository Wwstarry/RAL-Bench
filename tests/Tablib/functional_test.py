from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import pytest

# ---------------------------------------------------------------------------
# RACB import contract:
# 1) Import repo rooted at RACB_REPO_ROOT (runner sets it).
# 2) Auto-detect two layouts:
#    - repo_root/tablib/__init__.py
#    - repo_root/src/tablib/__init__.py  -> add repo_root/src to sys.path
# 3) Python 3.8/3.9 compatible typing.
#
# Local fallback:
# - If RACB_REPO_ROOT is not set, use TABLIB_TARGET to locate reference/generated.
# ---------------------------------------------------------------------------

PACKAGE_NAME = "tablib"
ROOT = Path(__file__).resolve().parents[2]


def _select_repo_root() -> Path:
    override = os.environ.get("RACB_REPO_ROOT", "").strip()
    if override:
        return Path(override).resolve()

    target = os.environ.get("TABLIB_TARGET", "reference").lower()
    if target == "reference":
        return (ROOT / "repositories" / "Tablib").resolve()
    if target == "generation":
        return (ROOT / "generation" / "Tablib").resolve()
    raise RuntimeError("Unsupported TABLIB_TARGET value: {}".format(target))


REPO_ROOT = _select_repo_root()
if not REPO_ROOT.exists():
    pytest.skip("Repository root does not exist: {}".format(REPO_ROOT), allow_module_level=True)

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

import tablib  # type: ignore  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_sample_dataset() -> "tablib.Dataset":
    """Create a small dataset with headers and a few rows for reuse."""
    headers = ("first_name", "last_name", "age")
    rows = [
        ("John", "Adams", 90),
        ("George", "Washington", 67),
        ("Ada", "Lovelace", 36),
    ]
    return tablib.Dataset(*rows, headers=headers)


def _normalize_dict_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Normalize dict rows for comparisons across formats/versions."""
    normalized: List[Dict[str, str]] = []
    for row in rows:
        normalized.append({k: str(v) for k, v in row.items()})
    return normalized


def _available_formats() -> List[str]:
    """Best-effort list of supported export/import formats, version-agnostic."""
    fmts: Any = None
    if hasattr(tablib, "formats"):
        fmts = getattr(tablib.formats, "available", None)
        if fmts is None:
            fmts = getattr(tablib.formats, "available_formats", None)
    if fmts is None:
        # Assume core formats exist in most implementations.
        return ["csv", "tsv", "json", "yaml", "html", "rst"]
    try:
        return list(fmts)
    except TypeError:
        return []


def _format_supported(fmt: str) -> bool:
    fmts = _available_formats()
    if not fmts:
        return True
    return fmt in fmts


def _iter_databook_sheets(book: "tablib.Databook") -> List["tablib.Dataset"]:
    """Return the sheets in a Databook across different Tablib versions."""
    if hasattr(book, "sheets"):
        sheets = book.sheets()
        return list(sheets)

    # Fallback to iteration if Databook implements __iter__.
    return list(book)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Tests (functional-only, happy path)  >= 10 test_* functions
# ---------------------------------------------------------------------------

def test_dataset_export_import_csv_and_json_roundtrip() -> None:
    """Exercise core CSV/JSON export and import roundtrips on Dataset."""
    data = _build_sample_dataset()

    # CSV roundtrip via export + .csv setter.
    csv_text = data.export("csv")
    assert isinstance(csv_text, str)

    loaded_csv = tablib.Dataset()
    loaded_csv.csv = csv_text

    assert loaded_csv.headers == data.headers
    assert loaded_csv.height == data.height
    assert loaded_csv.width == data.width

    orig_dict_norm = _normalize_dict_rows(data.dict)
    loaded_dict_norm = _normalize_dict_rows(loaded_csv.dict)
    assert loaded_dict_norm == orig_dict_norm

    # JSON roundtrip via export + .json setter.
    json_text = data.export("json")
    assert isinstance(json_text, str)

    parsed = json.loads(json_text)
    assert isinstance(parsed, list)
    assert len(parsed) == data.height

    loaded_json = tablib.Dataset()
    loaded_json.json = json_text
    assert loaded_json.headers == data.headers

    loaded_json_norm = _normalize_dict_rows(loaded_json.dict)
    assert loaded_json_norm == orig_dict_norm


def test_dataset_export_import_tsv_roundtrip() -> None:
    """TSV export/import should preserve shape and values (type-coercion tolerant)."""
    if not _format_supported("tsv"):
        pytest.skip("tsv format not available in this tablib build")

    data = _build_sample_dataset()
    tsv_text = data.export("tsv")
    assert isinstance(tsv_text, str)
    assert "\t" in tsv_text  # TSV delimiter signal

    loaded = tablib.Dataset()
    # Many Tablib builds support .tsv property; if not, export/import is still available.
    if hasattr(loaded, "tsv"):
        loaded.tsv = tsv_text  # type: ignore[attr-defined]
    else:
        # Use import hook by assigning to the generic format attribute if supported.
        loaded.import_set(tsv_text, format="tsv")  # type: ignore[attr-defined]

    assert loaded.headers == data.headers
    assert loaded.height == data.height
    assert loaded.width == data.width

    assert _normalize_dict_rows(loaded.dict) == _normalize_dict_rows(data.dict)


def test_dataset_csv_property_matches_export() -> None:
    """Dataset.csv (getter) should be consistent with export('csv')."""
    data = _build_sample_dataset()

    csv_a = data.export("csv")
    assert isinstance(csv_a, str)

    csv_b = getattr(data, "csv")
    assert isinstance(csv_b, str)

    # Allow minor trailing whitespace differences across versions.
    assert csv_a.strip() == csv_b.strip()
    assert "first_name" in csv_b
    assert "Ada" in csv_b


def test_dataset_row_column_operations_and_slicing() -> None:
    """Validate row appending, column appending, and slicing semantics."""
    data = tablib.Dataset()
    data.headers = ("city", "country")
    data.append(("Berlin", "DE"))
    data.append(("Paris", "FR"))
    data.append(("Tokyo", "JP"))

    populations = (3_500_000, 2_100_000, 13_900_000)
    data.append_col(populations, header="population")

    assert data.height == 3
    assert data.width == 3
    assert list(data.headers) == ["city", "country", "population"]

    first_two_rows = data[:2]
    assert len(first_two_rows) == 2
    assert first_two_rows[0][0] == "Berlin"

    cities = list(data["city"])
    assert cities == ["Berlin", "Paris", "Tokyo"]

    dict_rows = data.dict
    assert isinstance(dict_rows, list)
    assert dict_rows[0]["city"] == "Berlin"
    assert "population" in dict_rows[0]


def test_dataset_insert_and_pop_row_semantics() -> None:
    """Dataset should support inserting and popping rows (list-like usage)."""
    data = tablib.Dataset(headers=("id", "name"))
    data.append((1, "a"))
    data.append((3, "c"))

    # Insert a missing middle row.
    data.insert(1, (2, "b"))

    assert data.height == 3
    assert data[0] == (1, "a")
    assert data[1] == (2, "b")
    assert data[2] == (3, "c")

    last = data.pop()
    assert last == (3, "c")
    assert data.height == 2


def test_dataset_dict_representation_contains_expected_keys() -> None:
    """Dataset.dict should emit dict rows with all headers present."""
    data = _build_sample_dataset()
    rows = data.dict
    assert isinstance(rows, list)
    assert len(rows) == data.height

    first = rows[0]
    assert isinstance(first, dict)
    assert set(first.keys()) == set(data.headers)
    assert first["first_name"] == "John"


def test_dataset_title_and_headers_persistence() -> None:
    """Dataset title and headers should be assignable and remain consistent."""
    data = tablib.Dataset(headers=("k", "v"))
    data.title = "Config"
    data.append(("a", 1))
    data.append(("b", 2))

    assert getattr(data, "title") == "Config"
    assert tuple(data.headers) == ("k", "v")
    assert data.height == 2
    assert data[1][0] == "b"


def test_dataset_export_json_contains_all_records() -> None:
    """JSON export should serialize all dataset records in a list-like structure."""
    data = _build_sample_dataset()
    json_text = data.export("json")
    assert isinstance(json_text, str)

    parsed = json.loads(json_text)
    assert isinstance(parsed, list)
    assert len(parsed) == data.height

    # Ensure at least one known value is present in serialized output.
    joined = json.dumps(parsed)
    assert "Lovelace" in joined


def test_dataset_export_html_contains_table_structure() -> None:
    """HTML export (if available) should include a table-like structure and headers."""
    if not _format_supported("html"):
        pytest.skip("html format not available in this tablib build")

    data = _build_sample_dataset()
    html = data.export("html")
    assert isinstance(html, str)

    # Keep checks permissive across versions/formatters.
    lower = html.lower()
    assert "<table" in lower
    assert "first_name" in lower
    assert "ada" in lower


def test_databook_multi_sheet_json_roundtrip() -> None:
    """Databook should preserve sheet structure when exported/imported as JSON."""
    sheet1 = tablib.Dataset(
        (1, "a"),
        (2, "b"),
        headers=("id", "value"),
    )
    sheet1.title = "First"

    sheet2 = tablib.Dataset(
        (3, "c"),
        (4, "d"),
        headers=("id", "value"),
    )
    sheet2.title = "Second"

    book = tablib.Databook([sheet1, sheet2])

    json_text = book.export("json")
    assert isinstance(json_text, str)

    parsed = json.loads(json_text)
    assert isinstance(parsed, list)
    assert len(parsed) == 2

    loaded_book = tablib.Databook()
    loaded_book.json = json_text

    assert loaded_book.size == 2

    loaded_sheets = _iter_databook_sheets(loaded_book)
    assert len(loaded_sheets) == 2

    assert loaded_sheets[0].title == "First"
    assert loaded_sheets[1].title == "Second"
    assert loaded_sheets[0].headers == sheet1.headers
    assert loaded_sheets[1].headers == sheet2.headers

    assert _normalize_dict_rows(loaded_sheets[0].dict) == _normalize_dict_rows(sheet1.dict)
    assert _normalize_dict_rows(loaded_sheets[1].dict) == _normalize_dict_rows(sheet2.dict)


def test_databook_add_sheet_and_iteration_order() -> None:
    """Databook should allow adding sheets and preserve the order in iteration."""
    s1 = tablib.Dataset((1, "x"), headers=("id", "val"))
    s1.title = "S1"
    s2 = tablib.Dataset((2, "y"), headers=("id", "val"))
    s2.title = "S2"

    book = tablib.Databook([s1])

    if hasattr(book, "add_sheet"):
        book.add_sheet(s2)  # type: ignore[attr-defined]
    else:
        # Fallback: reconstruct via the public constructor (still normal usage).
        book = tablib.Databook([s1, s2])

    assert book.size == 2

    sheets = _iter_databook_sheets(book)
    assert len(sheets) == 2
    assert sheets[0].title == "S1"
    assert sheets[1].title == "S2"
    assert sheets[0][0] == (1, "x")
    assert sheets[1][0] == (2, "y")
