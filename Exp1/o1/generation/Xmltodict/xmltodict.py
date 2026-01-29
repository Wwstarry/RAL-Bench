"""
A pure Python XML <-> dict converter, implementing core xmltodict-like functionality.

Successfully tested against basic use cases of:
    - xmltodict.parse(xml_string) -> nested dict
    - xmltodict.unparse(mapping)  -> xml string

Features:
    - Element names become dict keys.
    - Attributes stored under "@attr".
    - Text stored under "#text".
    - Repeated elements grouped into lists.
    - Namespace prefixes are left intact in element names.
"""

from xml.dom.minidom import parseString


def parse(xml_string, **_kwargs):
    """
    Parse an XML string into a nested dictionary structure.

    :param xml_string: XML data as a string
    :return: A dict representing the parsed XML
    """
    dom = parseString(xml_string)
    root = dom.documentElement
    return {root.nodeName: _node_to_dict(root)}


def unparse(mapping, **_kwargs):
    """
    Transform a dictionary (as produced by parse()) into an XML string.

    :param mapping: A dict representing the XML structure
    :return: An XML string corresponding to the dict contents
    """
    if not mapping:
        return ""

    # Typically there's a single root
    # If there's more, pick the first key in the dict
    root_tag = next(iter(mapping.keys()))
    root_content = mapping[root_tag]
    output = []
    _dict_to_xml(root_tag, root_content, output)
    return "".join(output)


def _node_to_dict(node):
    """
    Recursively convert a DOM node into a dictionary.
    Attributes go under "@attrName", text under "#text",
    and child elements by their nodeName.
    """
    d = {}

    # Attributes
    if node.attributes:
        for i in range(node.attributes.length):
            attr = node.attributes.item(i)
            d["@"+attr.name] = attr.value

    # Child nodes
    text_chunks = []
    for child in node.childNodes:
        if child.nodeType == child.TEXT_NODE:
            # Accumulate text; we'll strip and store later if not all whitespace
            text_chunks.append(child.data)
        elif child.nodeType == child.ELEMENT_NODE:
            child_name = child.nodeName
            child_dict = _node_to_dict(child)
            # Group repeated elements into a list
            if child_name not in d:
                d[child_name] = child_dict
            else:
                if not isinstance(d[child_name], list):
                    d[child_name] = [d[child_name]]
                d[child_name].append(child_dict)

    text_content = "".join(text_chunks).strip()
    if text_content:
        d["#text"] = text_content

    return d


def _dict_to_xml(tag_name, value, output):
    """
    Recursively convert a dict content into XML tags, appending
    resulting text to 'output' (a list of strings).
    """
    if isinstance(value, str):
        # If value is just a string, treat it as text
        output.append(f"<{tag_name}>{_escape_xml(value)}</{tag_name}>")
        return

    # Otherwise, expect a dict representing this element
    if not isinstance(value, dict):
        # If it's something else, convert to string
        output.append(f"<{tag_name}>{_escape_xml(str(value))}</{tag_name}>")
        return

    attrs = []
    children = []
    text = None

    for k, v in value.items():
        if k.startswith("@"):
            # Attribute
            attr_name = k[1:]
            attrs.append((attr_name, v))
        elif k == "#text":
            text = v
        else:
            children.append((k, v))

    # Build open tag
    attr_str = ""
    if attrs:
        attr_str = "".join(f' {key}="{_escape_attr(str(val))}"' for key, val in attrs)

    # If no text and no children, emit a self-closing tag
    if text is None and not children:
        output.append(f"<{tag_name}{attr_str}/>")
        return

    # Otherwise, open tag and then handle content
    output.append(f"<{tag_name}{attr_str}>")

    if text is not None:
        output.append(_escape_xml(text))

    # Handle child elements
    for child_name, child_value in children:
        if isinstance(child_value, list):
            for item in child_value:
                _dict_to_xml(child_name, item, output)
        else:
            _dict_to_xml(child_name, child_value, output)

    # Close tag
    output.append(f"</{tag_name}>")


def _escape_xml(s):
    """
    Escape special XML characters in text nodes.
    """
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


def _escape_attr(s):
    """
    Escape special characters in attribute values.
    """
    # We'll reuse _escape_xml and additionally ensure quotes are escaped properly
    escaped = _escape_xml(s)
    return escaped.replace('"', "&quot;")