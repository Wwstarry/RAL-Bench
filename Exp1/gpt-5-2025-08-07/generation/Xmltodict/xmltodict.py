"""
A minimal XML parsing and serialization library that is API-compatible
with the core parts of the reference xmltodict project.

Public API:
- parse(xml_input, ...)
- unparse(mapping, ...)

Behavior:
- Element names become dictionary keys (namespace prefixes preserved).
- Attributes are stored under keys prefixed with attr_prefix (default "@").
- Text nodes are stored under text_key (default "#text").
- Repeated sibling elements are grouped into lists.
"""

from typing import Any, Callable, Dict, List, Optional, Union
import io
import xml.sax
from xml.sax.handler import ContentHandler


# Default key conventions matching xmltodict
DEFAULT_ATTR_PREFIX = "@"
DEFAULT_TEXT_KEY = "#text"


class _DictSAXHandler(ContentHandler):
    """
    A SAX ContentHandler that builds a nested mapping representation of XML.

    - Preserves qName (including namespace prefix) as element name.
    - Attributes are stored under keys with attr_prefix.
    - Text content is accumulated and stored under text_key.
    - Repeated siblings become lists.
    """

    def __init__(
        self,
        attr_prefix: str = DEFAULT_ATTR_PREFIX,
        text_key: str = DEFAULT_TEXT_KEY,
        dict_constructor: Callable[[], Dict[str, Any]] = dict,
        strip_whitespace: bool = True,
    ):
        super().__init__()
        self.attr_prefix = attr_prefix
        self.text_key = text_key
        self.dict_constructor = dict_constructor
        self.strip_whitespace = strip_whitespace

        # Stack of (name, node_dict)
        self._stack: List[tuple[str, Dict[str, Any]]] = []
        # Parallel stack of text buffers
        self._text_stack: List[List[str]] = []

        # Final result: {root_name: root_node}
        self.result: Optional[Dict[str, Any]] = None

    def startElement(self, name: str, attrs: xml.sax.xmlreader.AttributesImpl):
        node = self.dict_constructor()

        # Add attributes with prefix
        # Use getNames() to get qNames where possible
        try:
            names = attrs.getQNames()  # type: ignore[attr-defined]
            if names is None:
                names = attrs.getNames()
        except Exception:
            names = attrs.getNames()
        for k in names:
            try:
                v = attrs.getValue(k)
            except Exception:
                v = attrs.get(k)
            node[self.attr_prefix + k] = v

        self._stack.append((name, node))
        self._text_stack.append([])

    def characters(self, content: str):
        if not self._text_stack:
            return
        # Accumulate char data (SAX may split text)
        self._text_stack[-1].append(content)

    def endElement(self, name: str):
        # Pop current node
        name2, node = self._stack.pop()
        # Defensive: name should match
        # Finalize text for this node
        text_buffer = "".join(self._text_stack.pop())
        if self.strip_whitespace:
            text_clean = text_buffer.strip()
        else:
            text_clean = text_buffer

        if text_clean:
            node[self.text_key] = text_clean

        if self._stack:
            # Attach to parent as child
            parent_name, parent_node = self._stack[-1]
            existing = parent_node.get(name2)
            if existing is None:
                parent_node[name2] = node
            else:
                if isinstance(existing, list):
                    existing.append(node)
                else:
                    parent_node[name2] = [existing, node]
        else:
            # Root node completed
            self.result = {name2: node}


def parse(
    xml_input: Union[str, bytes, io.IOBase],
    encoding: Optional[str] = None,
    expat_cls: Any = None,   # accepted for compatibility; ignored
    process_namespaces: bool = False,  # accepted for compatibility; ignored (we preserve qNames)
    namespaces: Any = None,  # accepted for compatibility; ignored
    attr_prefix: str = DEFAULT_ATTR_PREFIX,
    cdata_key: Optional[str] = None,
    text_key: Optional[str] = None,
    dict_constructor: Callable[[], Dict[str, Any]] = dict,
    strip_whitespace: bool = True,
    **kwargs,
) -> Dict[str, Any]:
    """
    Parse an XML document into a nested Python dictionary.

    Parameters:
    - xml_input: XML string/bytes or a file-like object with .read().
    - encoding: Optional encoding to decode bytes; if None, attempts UTF-8 then default.
    - attr_prefix: Prefix for attribute keys (default "@").
    - text_key: Key to store text nodes (default "#text").
    - cdata_key: Alias for text_key; if provided, overrides text_key.
    - dict_constructor: Callable to construct new dicts (default dict).
    - strip_whitespace: If True, strips leading/trailing whitespace from text nodes.

    Returns:
    - A dictionary of the form {root_tag: {...}}.
    """
    # Resolve text key
    if text_key is None:
        text_key = DEFAULT_TEXT_KEY
    if cdata_key is not None:
        text_key = cdata_key

    # Acquire the XML as string
    data: Union[str, bytes]
    if hasattr(xml_input, "read"):
        data = xml_input.read()  # type: ignore
    else:
        data = xml_input  # type: ignore

    if isinstance(data, bytes):
        enc = encoding or "utf-8"
        try:
            xml_str = data.decode(enc)
        except Exception:
            # Fallback to default encoding if provided fails
            xml_str = data.decode()
    else:
        xml_str = str(data)

    # Setup SAX parser with namespaces disabled to preserve qName prefixes
    parser = xml.sax.make_parser()
    try:
        parser.setFeature(xml.sax.handler.feature_namespaces, False)
    except Exception:
        # If feature not supported, proceed; default CPython supports it
        pass

    handler = _DictSAXHandler(
        attr_prefix=attr_prefix,
        text_key=text_key,
        dict_constructor=dict_constructor,
        strip_whitespace=strip_whitespace,
    )
    parser.setContentHandler(handler)

    # Parse from in-memory string
    parser.parse(io.StringIO(xml_str))

    if handler.result is None:
        # Empty or invalid document
        return dict_constructor()

    return handler.result


def _escape_text(s: Any) -> str:
    if s is None:
        return ""
    # Convert to string and escape XML special chars for text nodes
    t = str(s)
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return t


def _escape_attr(s: Any) -> str:
    if s is None:
        return ""
    # Convert to string and escape for attribute context (quotes too)
    t = str(s)
    t = (
        t.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
    return t


def unparse(
    mapping: Dict[str, Any],
    output: Optional[io.IOBase] = None,
    encoding: Optional[str] = None,  # accepted for compatibility; ignored for str return
    full_document: bool = False,      # accepted for compatibility; if True, include XML declaration
    attr_prefix: str = DEFAULT_ATTR_PREFIX,
    text_key: str = DEFAULT_TEXT_KEY,
    pretty: bool = False,
    indent: str = "  ",
    short_empty_elements: bool = True,
    **kwargs,
) -> str:
    """
    Convert a mapping produced by parse() back to an XML string.

    Parameters:
    - mapping: A dict with a single root element key mapping to its content dict.
    - output: Optional file-like object to write XML into. If provided, returns None.
    - full_document: If True, includes an XML declaration at the start.
    - attr_prefix: Prefix for attribute keys (default "@").
    - text_key: Key used for text nodes (default "#text").
    - pretty: If True, pretty prints with indentation and newlines.
    - indent: Indentation string for pretty printing.
    - short_empty_elements: If True, emits "<tag/>" for empty elements.

    Returns:
    - XML string if output is None, else None.
    """
    # Validate mapping: expect one root element
    if not isinstance(mapping, dict) or len(mapping) != 1:
        raise ValueError("unparse() expects a dict with a single root element.")

    out_parts: List[str] = []

    if full_document:
        out_parts.append('<?xml version="1.0" encoding="{}"?>'.format(encoding or "UTF-8"))
        if pretty:
            out_parts.append("\n")

    # Serialization helpers
    def write(s: str):
        out_parts.append(s)

    def serialize_element(tag: str, value: Any, level: int):
        # If the value is a list, emit multiple elements with the same tag
        if isinstance(value, list):
            for item in value:
                serialize_element(tag, item, level)
            return

        # Determine attributes, text, and children
        attrs: Dict[str, Any] = {}
        text_val: Optional[Any] = None
        children: Dict[str, Any] = {}

        if isinstance(value, dict):
            for k, v in value.items():
                if k.startswith(attr_prefix):
                    attrs[k[len(attr_prefix) :]] = v
                elif k == text_key:
                    text_val = v
                else:
                    children[k] = v
        else:
            # Non-dict values treated as text-only content
            text_val = value

        # Build start tag with attributes
        if pretty:
            write(indent * level)

        write("<" + tag)
        for ak, av in attrs.items():
            write(f' {ak}="{_escape_attr(av)}"')

        # Decide on self-closing or normal element
        has_children = bool(children)
        has_text = text_val is not None and str(text_val) != ""

        if not has_children and not has_text:
            if short_empty_elements:
                write("/>")
                if pretty:
                    write("\n")
                return
            else:
                write("></" + tag + ">")
                if pretty:
                    write("\n")
                return

        write(">")

        # Emit text first (to keep representation straightforward)
        if has_text:
            write(_escape_text(text_val))

        # Emit children
        if has_children:
            if pretty:
                write("\n")
            # Maintain dict insertion order
            for ck, cv in children.items():
                serialize_element(ck, cv, level + 1)
            if pretty:
                write(indent * level)

        # End tag
        write("</" + tag + ">")
        if pretty:
            write("\n")

    # Serialize root
    root_tag = next(iter(mapping.keys()))
    root_value = mapping[root_tag]
    serialize_element(root_tag, root_value, 0)

    xml_output = "".join(out_parts)

    if output is not None:
        output.write(xml_output)
        return ""

    return xml_output


__all__ = ["parse", "unparse"]