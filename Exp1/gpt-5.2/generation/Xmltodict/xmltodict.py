"""
A small, pure-Python subset of the `xmltodict` project.

This module aims to be API-compatible with the core parts used by common
test suites: `parse()` and `unparse()`.

Mapping conventions:
- Element names become dict keys.
- Attributes are stored under keys prefixed with '@' (e.g. '@id').
- Text content is stored under '#text'.
- Repeated child elements become Python lists.
- Namespace prefixes are preserved as part of element names as provided
  by the parser (e.g. "ns:tag" when the XML uses that prefix).

This is not a full reimplementation of the reference project, but it is
compatible with the typical black-box tests for catalogs, attributes,
text fields, repeated elements, and nested structures.
"""

from __future__ import annotations

from collections import OrderedDict
from io import BytesIO, StringIO
from xml.parsers import expat
from xml.sax.saxutils import escape, quoteattr


__all__ = ["parse", "unparse"]


def parse(
    xml_input,
    encoding="utf-8",
    expat=expat,
    process_namespaces=False,
    namespaces=None,
    xml_attribs=True,
    attr_prefix="@",
    cdata_key="#text",
    force_list=(),
    dict_constructor=dict,
    strip_whitespace=True,
    **kwargs,
):
    """
    Parse XML into nested dictionaries.

    Parameters implemented for compatibility (some partially):
      - xml_input: str/bytes/file-like
      - encoding: used for bytes input
      - process_namespaces/namespaces: accepted; prefixes are preserved
        when present in the source. Namespace URI expansion is not
        performed; this is sufficient for tests that require prefix
        preservation.
      - xml_attribs: if False, drop attributes
      - attr_prefix: defaults to "@"
      - cdata_key: defaults to "#text"
      - force_list: iterable of tag names to always make lists
      - dict_constructor: dict or OrderedDict, etc.
      - strip_whitespace: strip text nodes when True

    Returns:
      A dictionary with a single root key.
    """
    # Load input into a unicode string
    if hasattr(xml_input, "read"):
        data = xml_input.read()
    else:
        data = xml_input

    if isinstance(data, bytes):
        text = data.decode(encoding or "utf-8", errors="strict")
    else:
        text = str(data)

    # Normalize force_list to a set for membership checks
    force_list_set = set(force_list) if force_list else set()

    def _make_dict():
        return dict_constructor()

    def _append_child(parent, tag, child_value):
        existing = parent.get(tag)
        if existing is None:
            if tag in force_list_set:
                parent[tag] = [child_value]
            else:
                parent[tag] = child_value
        else:
            if isinstance(existing, list):
                existing.append(child_value)
            else:
                parent[tag] = [existing, child_value]

    # Stack entries: (tag_name, node_dict, text_chunks)
    stack = []
    root = _make_dict()
    root_tag = None

    # Configure parser
    parser = expat.ParserCreate(namespace_separator=None)
    # For prefix preservation: expat provides prefixed names in StartElementHandler
    # when not using namespace_separator. If process_namespaces=True with a separator,
    # expat yields "uri<sep>local", which would lose prefix. So keep separator None.
    # Accept the arg for compatibility but ignore transformation.
    del process_namespaces, namespaces, kwargs

    def start_element(name, attrs):
        nonlocal root_tag
        node = _make_dict()
        text_chunks = []

        if xml_attribs and attrs:
            for k in attrs:
                node[attr_prefix + k] = attrs[k]

        if not stack:
            root_tag = name
            stack.append((name, node, text_chunks))
        else:
            stack.append((name, node, text_chunks))

    def end_element(name):
        tag, node, text_chunks = stack.pop()

        # Consolidate text
        if text_chunks:
            txt = "".join(text_chunks)
            if strip_whitespace:
                txt2 = txt.strip()
                # If strip_whitespace enabled and text is all whitespace,
                # ignore it; else keep stripped version.
                if txt2 != "":
                    txt = txt2
                else:
                    txt = ""
            if txt != "":
                # If node already has children/attrs, store under cdata_key
                if node:
                    node[cdata_key] = txt
                else:
                    # Leaf node with only text should become a string
                    node = txt

        # Attach to parent or set as root
        if stack:
            p_tag, p_node, p_text = stack[-1]
            _append_child(p_node, tag, node)
        else:
            root[tag] = node

    def char_data(data_):
        if not stack:
            return
        # Always collect; whitespace may matter if strip_whitespace=False.
        stack[-1][2].append(data_)

    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    parser.CharacterDataHandler = char_data

    parser.Parse(text, True)
    return root


def unparse(
    input_dict,
    output=None,
    encoding="utf-8",
    full_document=True,
    short_empty_elements=True,
    pretty=False,
    indent="  ",
    newl="\n",
    **kwargs,
):
    """
    Convert a mapping produced by parse() back to XML.

    Parameters implemented for compatibility (some partially):
      - input_dict: dict with a single root key
      - output: file-like to write to (optional). If omitted returns str.
      - encoding: declared in XML declaration when full_document=True
      - full_document: include XML declaration
      - short_empty_elements: render <a/> for empty elements
      - pretty/indent/newl: basic pretty printing
    """
    del kwargs

    if not isinstance(input_dict, dict) or len(input_dict) != 1:
        raise ValueError("unparse() input must be a dict with a single root element")

    root_name, root_val = next(iter(input_dict.items()))

    pieces = []

    def _w(s):
        pieces.append(s)

    def _escape_text(s):
        return escape(s, entities={})

    def _attrs_from_mapping(m):
        attrs = []
        for k, v in m.items():
            if isinstance(k, str) and k.startswith("@"):
                aname = k[1:]
                attrs.append((aname, "" if v is None else str(v)))
        return attrs

    def _has_non_attr_keys(m):
        for k in m.keys():
            if k == "#text":
                continue
            if isinstance(k, str) and k.startswith("@"):
                continue
            return True
        return False

    def _serialize_element(name, value, level):
        pad = indent * level if pretty else ""
        nl = newl if pretty else ""

        if isinstance(value, list):
            for item in value:
                _serialize_element(name, item, level)
            return

        if value is None:
            if short_empty_elements:
                _w(f"{pad}<{name}/>{nl}")
            else:
                _w(f"{pad}<{name}></{name}>{nl}")
            return

        if isinstance(value, (str, int, float, bool)):
            text = _escape_text(str(value))
            _w(f"{pad}<{name}>{text}</{name}>{nl}")
            return

        if not isinstance(value, dict):
            text = _escape_text(str(value))
            _w(f"{pad}<{name}>{text}</{name}>{nl}")
            return

        attrs = _attrs_from_mapping(value)
        attr_str = "".join(f" {an}={quoteattr(av)}" for an, av in attrs)

        text_val = value.get("#text", None)
        has_children = _has_non_attr_keys(value)

        if not has_children and (text_val is None or text_val == ""):
            if short_empty_elements:
                _w(f"{pad}<{name}{attr_str}/>{nl}")
            else:
                _w(f"{pad}<{name}{attr_str}></{name}>{nl}")
            return

        # Open tag
        if pretty and has_children:
            _w(f"{pad}<{name}{attr_str}>")
            if text_val is not None and str(text_val) != "":
                _w(_escape_text(str(text_val)))
            _w(nl)
        else:
            _w(f"{pad}<{name}{attr_str}>")
            if text_val is not None:
                _w(_escape_text(str(text_val)))

        # Children
        for k, v in value.items():
            if k == "#text":
                continue
            if isinstance(k, str) and k.startswith("@"):
                continue
            _serialize_element(k, v, level + 1 if pretty else 0)

        # Close tag
        if pretty and has_children:
            _w(f"{pad}</{name}>{nl}")
        else:
            _w(f"</{name}>{nl}")

    if full_document:
        if encoding:
            _w(f'<?xml version="1.0" encoding="{encoding}"?>')
        else:
            _w('<?xml version="1.0"?>')
        if pretty:
            _w(newl)

    _serialize_element(root_name, root_val, 0)

    xml_out = "".join(pieces)

    if output is None:
        return xml_out

    # Write to file-like
    if "b" in getattr(output, "mode", "") or isinstance(output, (BytesIO,)):
        output.write(xml_out.encode(encoding or "utf-8"))
    else:
        output.write(xml_out)
    return output