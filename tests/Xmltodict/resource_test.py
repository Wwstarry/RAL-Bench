from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

ROOT = Path(__file__).resolve().parents[2]

# Decide whether to test the reference repo or a generated repo.
target = os.environ.get("XMLTODICT_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "xmltodict"
else:
    REPO_ROOT = ROOT / "generation" / "Xmltodict"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import xmltodict  # type: ignore  # noqa: E402


_COMPLEX_XML = """
<catalog>
  <book id="bk101">
    <author>Gambardella, Matthew</author>
    <title>XML Developer's Guide</title>
    <genre>Computer</genre>
    <price currency="USD">44.95</price>
    <publish_date>2000-10-01</publish_date>
    <description>An in-depth look at creating applications with XML.</description>
  </book>
  <book id="bk102">
    <author>Ralls, Kim</author>
    <title>Midnight Rain</title>
    <genre>Fantasy</genre>
    <price currency="USD">5.95</price>
    <publish_date>2000-12-16</publish_date>
    <description>A former architect battles corporate zombies.</description>
  </book>
</catalog>
""".strip()


def _parse_catalog() -> Dict[str, Any]:
    """Parse the complex catalog XML into a Python dict."""
    return xmltodict.parse(_COMPLEX_XML)


def test_catalog_structure_and_types() -> None:
    """The parsed catalog should have the expected nested structure and types."""
    data = _parse_catalog()

    assert "catalog" in data
    catalog = data["catalog"]
    assert "book" in catalog

    books = catalog["book"]
    assert isinstance(books, list)
    assert len(books) == 2

    first = books[0]
    assert first["@id"] == "bk101"
    assert first["author"].startswith("Gambardella")
    assert first["price"]["@currency"] == "USD"
    assert float(first["price"]["#text"]) > 0.0


def test_roundtrip_complex_catalog() -> None:
    """
    Parsing and then unparsing the complex catalog XML should preserve
    the logical structure when parsed again.
    """
    original_dict = _parse_catalog()

    xml = xmltodict.unparse(original_dict)
    round_tripped = xmltodict.parse(xml)

    assert round_tripped == original_dict
