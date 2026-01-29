"""
A lightweight subset re-implementation of the most common APIs of the
excellent ``xmltodict`` library.

Only what is required for the accompanying test-suite is implemented
here:

    * xmltodict.parse(xml_string, ...)
    * xmltodict.unparse(mapping, ...)

Behavioural goals (compatible with the reference implementation for the
covered use-cases):

    • XML elements become dictionary entries whose key is the element
      name (namespace prefix, if any, is preserved).

    • XML attributes are stored under keys prefixed with ``@`` (configurable
      through *attr_prefix*).

    • Text content goes under key ``#text`` (configurable through
      *cdata_key*).

    • Repeated sibling elements are gathered into a list.

    • The inverse operation ``unparse`` recreates an XML string that, when
      parsed again, yields a structure equivalent to the original mapping.

Only the Python standard library is required.
"""
from __future__ import annotations

import collections
import io
import sys
import xml.etree.ElementTree as _ET
from xml.dom import minidom
from typing import Any, Mapping, MutableMapping, Union, List


__all__ = ["parse", "unparse"]


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #
_TextTypes = (str, int, float, bool)


def _is_text_node(obj: Any) -> bool:
    """Return ``True`` if *obj* should be treated as a leaf text node."""
    return isinstance(obj, _TextTypes)


# --------------------------------------------------------------------------- #
#  PARSE                                                                      #
# --------------------------------------------------------------------------- #
def parse(
    xml_input: Union[str, bytes, io.IOBase],
    *,
    attr_prefix: str = "@",
    cdata_key: str = "#text",
    dict_constructor: type = collections.OrderedDict,
    encoding: str | None = "utf-8",
) -> Mapping[str, Any]:
    """
    Parse *xml_input* into a nested mapping.

    Parameters
    ----------
    xml_input
        XML document given as ``str``/``bytes`` or as any file-like object
        providing ``.read()``.
    attr_prefix
        Prefix applied to attribute keys (default ``'@'``).
    cdata_key
        Key used for text nodes (default ``'#text'``).
    dict_constructor
        Type used for newly created mappings.  ``collections.OrderedDict`` by
        default to preserve element order.
    encoding
        Character encoding used when *xml_input* is *bytes* or a file-like
        object opened in *binary* mode.

    Returns
    -------
    Mapping
        A mapping describing the XML document.
    """
    # ------------------------------------------------------------------ #
    # Obtain the XML string                                              #
    # ------------------------------------------------------------------ #
    if hasattr(xml_input, "read"):
        # file-like object
        data = xml_input.read()
    else:
        data = xml_input

    if isinstance(data, bytes):
        xml_string: str = data.decode(encoding or "utf-8", errors="replace")
    else:
        xml_string = data

    # ------------------------------------------------------------------ #
    # Recursively convert the ElementTree into dictionaries              #
    # ------------------------------------------------------------------ #
    root: _ET.Element = _ET.fromstring(xml_string)

    def _convert(el: _ET.Element) -> Mapping[str, Any]:
        """
        Convert *el* into mapping according to the rules described above and
        return ``{el.tag: value}``.
        """
        node_map: MutableMapping[str, Any] = dict_constructor()

        # Attributes ---------------------------------------------------- #
        for k, v in el.attrib.items():
            node_map[f"{attr_prefix}{k}"] = v

        # Children ------------------------------------------------------ #
        for child in el:
            child_mapping = _convert(child)
            tag, value = next(iter(child_mapping.items()))

            if tag in node_map:
                existing = node_map[tag]
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    node_map[tag] = [existing, value]
            else:
                node_map[tag] = value

        # Text ---------------------------------------------------------- #
        text = (el.text or "").strip()
        if text:
            if node_map:
                node_map[cdata_key] = text
            else:
                # No attributes/children – represent directly as text
                return dict_constructor(((el.tag, text),))

        return dict_constructor(((el.tag, node_map)))

    return _convert(root)


# --------------------------------------------------------------------------- #
#  UNPARSE                                                                    #
# --------------------------------------------------------------------------- #
def unparse(
    data_dict: Mapping[str, Any],
    *,
    attr_prefix: str = "@",
    cdata_key: str = "#text",
    pretty: bool = False,
    full_document: bool = False,
    encoding: str = "utf-8",
) -> str:
    """
    Convert a *data_dict* produced by :pyfunc:`parse` back into an XML string.

    Parameters
    ----------
    data_dict
        Mapping describing the XML document.
    attr_prefix
        Prefix that marks attribute keys (must match what was used for parsing).
    cdata_key
        Key that holds text nodes (must match what was used for parsing).
    pretty
        If *True*, return human readable, indented XML.
    full_document
        If *True*, include an ``<?xml version="1.0"?>`` declaration.
    encoding
        Encoding of resulting string (utf-8 by default).

    Returns
    -------
    str
        XML representation.
    """
    if not isinstance(data_dict, Mapping) or len(data_dict) != 1:
        raise ValueError("data_dict must have exactly one root element")

    root_tag, root_val = next(iter(data_dict.items()))
    root_el = _ET.Element(root_tag)

    def _build(element: _ET.Element, value: Any) -> None:
        """
        Build subtree under *element* from *value* which may be:
            • Mapping  – element with attributes/children
            • list     – repeated child elements
            • scalar   – text node
        """
        # Mapping -------------------------------------------------------- #
        if isinstance(value, Mapping):
            # First attributes + text so they appear before children if order
            # matters anywhere (this matches how parse() will re-generate the
            # dict).
            for k in value:
                if k.startswith(attr_prefix):
                    element.set(k[len(attr_prefix) :], str(value[k]))

            if cdata_key in value and not any(
                isinstance(v, Mapping) or isinstance(v, list)
                for kk, v in value.items()
                if not kk.startswith(attr_prefix) and kk != cdata_key
            ):
                # Element has text only (plus possible attributes)
                element.text = str(value[cdata_key])

            # Children --------------------------------------------------- #
            for k, v in value.items():
                if k.startswith(attr_prefix) or k == cdata_key:
                    continue  # already dealt with

                if isinstance(v, list):
                    for item in v:
                        child_el = _ET.SubElement(element, k)
                        _build(child_el, item)
                else:
                    child_el = _ET.SubElement(element, k)
                    _build(child_el, v)

        # List ----------------------------------------------------------- #
        elif isinstance(value, list):
            # For lists we cannot attach directly to *element*; caller must have
            # created appropriate child elements already.  Still, handle for
            # robustness by creating anonymous items with the same tag as parent.
            for item in value:
                child_el = _ET.SubElement(element, element.tag)
                _build(child_el, item)

        # Scalar --------------------------------------------------------- #
        else:
            element.text = str(value)

    _build(root_el, root_val)

    # ------------------------------------------------------------------ #
    # Serialise                                                          #
    # ------------------------------------------------------------------ #
    raw_bytes: bytes = _ET.tostring(root_el, encoding=encoding)

    if pretty:
        # ``minidom`` re-parses to produce nicely indented output
        parsed = minidom.parseString(raw_bytes)
        xml_string = parsed.toprettyxml(indent="  ", encoding=encoding)
        result = xml_string.decode(encoding)
    else:
        result = raw_bytes.decode(encoding)

    if full_document and not result.lstrip().startswith("<?xml"):
        declaration = f'<?xml version="1.0" encoding="{encoding}"?>'
        result = f"{declaration}\n{result}"

    return result


# --------------------------------------------------------------------------- #
#  Module test (executed when run directly)                                   #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # A quick, very small self-test for sanity
    xml = """
    <catalog>
        <book id="bk101">
            <author>Gambardella, Matthew</author>
            <title>XML Developer's Guide</title>
            <price>44.95</price>
        </book>
        <book id="bk102">
            <author>Ralls, Kim</author>
            <title>Midnight Rain</title>
            <price>5.95</price>
        </book>
    </catalog>
    """
    data = parse(xml)
    print("Parsed mapping:")
    print(data)

    xml2 = unparse(data, pretty=True)
    print("Re-generated XML:")
    print(xml2)

    # Round-trip check
    assert parse(xml2) == data, "Round-trip failed"
    print("Round-trip successful.")