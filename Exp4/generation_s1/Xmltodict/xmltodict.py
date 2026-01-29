"""
A tiny pure-Python subset of the `xmltodict` project.

Implements:
    - parse(xml_input, ...)
    - unparse(mapping, ...)

Core behaviors targeted by the test-suite:
    * element names as keys (namespace prefixes preserved when present)
    * attributes under "@attr" keys
    * text content under "#text" (or scalar string when element is text-only)
    * repeated elements grouped into lists
    * namespace declarations (xmlns / xmlns:prefix) are NOT exposed as attributes
"""

from __future__ import annotations

from collections.abc import Mapping
from io import StringIO
import xml.sax
from xml.sax.handler import ContentHandler
from xml.sax.saxutils import XMLGenerator, escape, quoteattr


def _coerce_input_to_stream(xml_input, encoding: str):
    if hasattr(xml_input, "read"):
        return xml_input
    if isinstance(xml_input, bytes):
        return StringIO(xml_input.decode(encoding))
    if isinstance(xml_input, str):
        return StringIO(xml_input)
    raise TypeError("xml_input must be str, bytes, or a file-like object")


def _add_child(container: dict, key: str, value):
    if key in container:
        existing = container[key]
        if isinstance(existing, list):
            existing.append(value)
        else:
            container[key] = [existing, value]
    else:
        container[key] = value


def _finalize_text(chunks):
    if not chunks:
        return ""
    return "".join(chunks)


def _is_all_whitespace(s: str) -> bool:
    return s.strip() == ""


def _attrs_to_mapping(attrs):
    """
    Convert SAX Attributes into our mapping:
      - regular attributes => {"@name": "value"}
      - xmlns declarations are ignored (not surfaced), matching xmltodict behavior.
    """
    out = {}
    # attrs can be AttributesImpl; qNames present in attrs.getQNames()
    try:
        qnames = list(attrs.getQNames())
        getter = attrs.getValue
    except Exception:
        qnames = list(attrs.keys())
        getter = attrs.get
    for qn in qnames:
        # Drop namespace declaration attributes
        # SAX reports xmlns declarations as attributes, and tests expect them excluded.
        if qn == "xmlns" or qn.startswith("xmlns:"):
            continue
        out["@" + qn] = getter(qn)
    return out


class _DictSAXHandler(ContentHandler):
    def __init__(self):
        super().__init__()
        self._stack = []  # list of (name, obj_dict, text_chunks, has_children_flag)
        self.result = None

    def startElement(self, name, attrs):
        node = {}
        node.update(_attrs_to_mapping(attrs))
        self._stack.append([name, node, [], False])

    def endElement(self, name):
        _name, node, text_chunks, has_children = self._stack.pop()
        text = _finalize_text(text_chunks)

        # Heuristic: if element has children and text is indentation-only, drop it
        if has_children and _is_all_whitespace(text):
            text = ""

        # Decide representation
        has_attrs = any(k.startswith("@") for k in node.keys())
        has_other_keys = any(not k.startswith("@") for k in node.keys())

        if has_other_keys:
            # children already present
            if text != "":
                node["#text"] = text
            value = node
        else:
            # no children
            if has_attrs:
                if text != "":
                    node["#text"] = text
                value = node
            else:
                if text == "":
                    value = None
                else:
                    value = text

        if not self._stack:
            self.result = {_name: value}
            return

        parent_name, parent_node, parent_text_chunks, parent_has_children = self._stack[-1]
        parent_has_children = True
        self._stack[-1][3] = True  # has_children
        _add_child(parent_node, _name, value)

    def characters(self, content):
        if not self._stack:
            return
        name, node, text_chunks, has_children = self._stack[-1]
        # Drop indentation-only chunks if we already have children
        if has_children and _is_all_whitespace(content):
            return
        text_chunks.append(content)


def parse(
    xml_input,
    encoding="utf-8",
    expat=None,
    process_namespaces=False,
    namespace_separator=":",
    disable_entities=True,
    **kwargs,
):
    """
    Parse XML into a nested dict/list structure.
    Unknown kwargs are accepted for compatibility and ignored.
    """
    stream = _coerce_input_to_stream(xml_input, encoding)
    handler = _DictSAXHandler()

    parser = xml.sax.make_parser()
    # Best-effort security hardening: disable external entity processing where supported.
    if disable_entities:
        for feat in (
            xml.sax.handler.feature_external_ges,
            xml.sax.handler.feature_external_pes,
        ):
            try:
                parser.setFeature(feat, False)
            except Exception:
                pass

    # We prefer qName-preserving callbacks (startElement/endElement).
    # Enabling namespaces would switch to startElementNS/endElementNS, losing prefixes.
    try:
        parser.setFeature(xml.sax.handler.feature_namespaces, False)
    except Exception:
        pass

    parser.setContentHandler(handler)
    parser.parse(stream)
    return handler.result


def _escape_text(s: str) -> str:
    return escape(s, entities={})


def _escape_attr_value(s: str) -> str:
    # quoteattr returns quoted string; we'll just use it directly where needed
    return s


def _to_str(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def _emit_element(name, value, out, short_empty_elements=True):
    if isinstance(value, list):
        for item in value:
            _emit_element(name, item, out, short_empty_elements=short_empty_elements)
        return

    # Element with complex content
    if isinstance(value, Mapping):
        # attributes
        attrs = []
        text = None
        children = []

        for k, v in value.items():
            if k.startswith("@"):
                aname = k[1:]
                # Skip xmlns declarations if present in mapping to keep parse/unparse stable
                if aname == "xmlns" or aname.startswith("xmlns:"):
                    continue
                attrs.append((aname, _to_str(v)))
            elif k == "#text":
                text = _to_str(v)
            else:
                children.append((k, v))

        attr_str = "".join(f" {aname}={quoteattr(aval)}" for aname, aval in attrs)

        if not children and (text is None or text == ""):
            if short_empty_elements:
                out.write(f"<{name}{attr_str}/>")
            else:
                out.write(f"<{name}{attr_str}></{name}>")
            return

        out.write(f"<{name}{attr_str}>")
        if text is not None:
            out.write(_escape_text(text))
        for ck, cv in children:
            _emit_element(ck, cv, out, short_empty_elements=short_empty_elements)
        out.write(f"</{name}>")
        return

    # Scalar text or empty
    if value is None:
        if short_empty_elements:
            out.write(f"<{name}/>")
        else:
            out.write(f"<{name}></{name}>")
    else:
        out.write(f"<{name}>{_escape_text(_to_str(value))}</{name}>")


def unparse(
    input_dict,
    output=None,
    encoding="utf-8",
    full_document=True,
    short_empty_elements=True,
    **kwargs,
):
    """
    Serialize mapping/list/scalars to XML.
    Unknown kwargs are accepted for compatibility and ignored.
    """
    if not isinstance(input_dict, Mapping):
        raise TypeError("input_dict must be a mapping (dict-like)")

    buf = output if output is not None else StringIO()

    if full_document:
        buf.write(f'<?xml version="1.0" encoding="{encoding}"?>')

    # Expect a single root element
    if len(input_dict) != 1:
        # Best-effort: emit each top-level key (non-standard but avoids crashing)
        for k, v in input_dict.items():
            _emit_element(k, v, buf, short_empty_elements=short_empty_elements)
    else:
        (root_name, root_val), = input_dict.items()
        _emit_element(root_name, root_val, buf, short_empty_elements=short_empty_elements)

    if output is None:
        return buf.getvalue()
    return None