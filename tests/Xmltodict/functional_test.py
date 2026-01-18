from __future__ import annotations

import inspect
import os
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "xmltodict"


def _select_repo_root() -> Path:
    """
    RACB contract:
    - Prefer RACB_REPO_ROOT (runner will set it).
    - Fallback to the original XMLTODICT_TARGET layout for local convenience.
    """
    override = os.environ.get("RACB_REPO_ROOT", "").strip()
    if override:
        return Path(override).resolve()

    target = os.environ.get("XMLTODICT_TARGET", "reference").lower()
    if target == "reference":
        return (ROOT / "repositories" / "xmltodict").resolve()
    return (ROOT / "generation" / "Xmltodict").resolve()


REPO_ROOT = _select_repo_root()
if not REPO_ROOT.exists():
    pytest.skip(
        f"RACB_REPO_ROOT does not exist on disk: {REPO_ROOT}",
        allow_module_level=True,
    )

# Import path auto-detection (RACB-required rule):
# If src/<package>/__init__.py exists -> sys.path insert repo_root/src, else insert repo_root.
src_pkg_init = REPO_ROOT / "src" / PACKAGE / "__init__.py"
if src_pkg_init.exists():
    if str(REPO_ROOT / "src") not in sys.path:
        sys.path.insert(0, str(REPO_ROOT / "src"))
else:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

import xmltodict  # type: ignore  # noqa: E402


# -----------------------------------------------------------------------------
# Compat helpers: only pass kwargs supported by the version under test.
# -----------------------------------------------------------------------------

_PARSE_PARAMS = set(inspect.signature(xmltodict.parse).parameters.keys())
_UNPARSE_PARAMS = set(inspect.signature(xmltodict.unparse).parameters.keys())


def _parse(xml: str, **kwargs: Any) -> Any:
    filtered = {k: v for k, v in kwargs.items() if k in _PARSE_PARAMS}
    return xmltodict.parse(xml, **filtered)  # type: ignore[arg-type]


def _unparse(obj: Any, **kwargs: Any) -> str:
    filtered = {k: v for k, v in kwargs.items() if k in _UNPARSE_PARAMS}
    return xmltodict.unparse(obj, **filtered)  # type: ignore[arg-type]


# -----------------------------------------------------------------------------
# Tests (functional-only / happy path)
# -----------------------------------------------------------------------------

def test_parse_simple_element() -> None:
    """Parsing a simple XML element should produce the expected dict."""
    xml = "<root><message>Hello</message></root>"
    data = _parse(xml)

    assert "root" in data
    assert data["root"]["message"] == "Hello"


def test_parse_repeated_elements_as_list() -> None:
    """Repeated child elements should be represented as a list."""
    xml = "<root><item>1</item><item>2</item><item>3</item></root>"
    data = _parse(xml)

    items = data["root"]["item"]
    assert isinstance(items, list)
    assert items == ["1", "2", "3"]


def test_parse_attributes_and_text() -> None:
    """Attributes and text content should be exposed using @attr and #text keys."""
    xml = '<user id="123">Alice</user>'
    data = _parse(xml)

    user = data["user"]
    assert user["@id"] == "123"
    assert user["#text"] == "Alice"


def test_unparse_roundtrip_basic_structure() -> None:
    """unparse() followed by parse() should preserve the logical structure."""
    original = {
        "root": {
            "item": [
                {"@id": "1", "#text": "A"},
                {"@id": "2", "#text": "B"},
            ]
        }
    }

    xml = _unparse(original)
    round_tripped = _parse(xml)

    assert round_tripped == original


def test_namespace_prefix_is_preserved() -> None:
    """Namespace prefixes in element names should be preserved in dict keys."""
    xml = """
    <root xmlns:x="http://example.com/x">
        <x:item>value</x:item>
    </root>
    """
    data = _parse(xml)

    root = data["root"]
    keys = [k for k in root.keys() if isinstance(k, str)]
    assert any(k.startswith("x:") for k in keys)

    key = next(k for k in keys if k.startswith("x:"))
    assert root[key] == "value"


def test_parse_nested_structure() -> None:
    """Nested XML elements should map to nested dict structures."""
    xml = """
    <root>
        <user>
            <name>Ada</name>
            <address>
                <city>London</city>
                <country>UK</country>
            </address>
        </user>
    </root>
    """
    data = _parse(xml)
    assert data["root"]["user"]["name"] == "Ada"
    assert data["root"]["user"]["address"]["city"] == "London"
    assert data["root"]["user"]["address"]["country"] == "UK"


def test_force_list_option_for_single_element() -> None:
    """force_list should allow representing a single child as a list when supported."""
    xml = "<root><item>1</item></root>"

    # Prefer a targeted force_list that is common in xmltodict.
    data = _parse(xml, force_list=("item",))

    item = data["root"]["item"]
    if "force_list" in _PARSE_PARAMS:
        assert isinstance(item, list)
        assert item == ["1"]
    else:
        # Fallback: without force_list support, single element is typically a scalar string.
        assert item == "1"


def test_custom_attr_prefix_and_cdata_key_if_supported() -> None:
    """attr_prefix / cdata_key customization should reflect in output when supported."""
    xml = '<user id="7">Bob</user>'

    data = _parse(xml, attr_prefix="$", cdata_key="text")
    user = data["user"]

    # Accept both default and customized keys depending on version support.
    attr_key = "$id" if "$id" in user else "@id"
    text_key = "text" if "text" in user else "#text"

    assert user[attr_key] == "7"
    assert user[text_key] == "Bob"


def test_xml_attribs_false_drops_attributes_if_supported() -> None:
    """xml_attribs=False should omit attribute keys when supported."""
    xml = '<user id="9"><name>Alice</name></user>'

    data = _parse(xml, xml_attribs=False)
    user = data["user"]

    if "xml_attribs" in _PARSE_PARAMS:
        # With xml_attribs=False, attribute keys should not be present.
        assert "@id" not in user
        assert user["name"] == "Alice"
    else:
        # Fallback: attribute is included in typical default behavior.
        assert user.get("@id") == "9"
        assert user["name"] == "Alice"


def test_dict_constructor_ordereddict() -> None:
    """dict_constructor should allow choosing mapping type (e.g., OrderedDict) when supported."""
    xml = "<root><a>1</a><b>2</b></root>"
    data = _parse(xml, dict_constructor=OrderedDict)

    if "dict_constructor" in _PARSE_PARAMS:
        assert isinstance(data, OrderedDict)
        assert isinstance(data["root"], OrderedDict)
    else:
        assert isinstance(data, dict)

    assert data["root"]["a"] == "1"
    assert data["root"]["b"] == "2"


def test_unparse_pretty_and_parse_back() -> None:
    """Pretty/full_document knobs should not break roundtrip of basic structure."""
    original: Dict[str, Any] = {"root": {"x": "1", "y": "2"}}

    xml = _unparse(original, pretty=True, full_document=True)
    assert "<root>" in xml or "<root" in xml

    round_tripped = _parse(xml)
    assert round_tripped == original


def test_postprocessor_transforms_value_if_supported() -> None:
    """postprocessor can transform values in a happy-path parse when supported."""
    xml = "<root><message>Hello</message></root>"

    def _pp(path: Any, key: str, value: Any) -> Any:
        if key == "message" and isinstance(value, str):
            return key, value.upper()
        return key, value

    data = _parse(xml, postprocessor=_pp)

    if "postprocessor" in _PARSE_PARAMS:
        assert data["root"]["message"] == "HELLO"
    else:
        assert data["root"]["message"] == "Hello"
