"""
A pure Python XML parsing and serialization library with an API
compatible with the core of the xmltodict library.
"""

import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET

__all__ = ['parse', 'unparse']

# ==============================================================================
# Internal helper functions for parsing (minidom -> dict)
# ==============================================================================

def _is_text_node(node):
    """Check if a minidom node is a non-empty text node."""
    return node.nodeType == node.TEXT_NODE and node.data.strip()

def _parse_node(node):
    """
    Recursively convert a minidom node and its children into a dictionary
    or a simple value.
    """
    result = {}

    # Add attributes to the dictionary
    if node.attributes:
        for i in range(node.attributes.length):
            attr = node.attributes.item(i)
            result['@' + attr.name] = attr.value

    # Process child elements
    children = [n for n in node.childNodes if n.nodeType == n.ELEMENT_NODE]
    if children:
        child_map = {}
        for child in children:
            tag = child.tagName
            content = _parse_node(child)
            if tag not in child_map:
                child_map[tag] = []
            child_map[tag].append(content)
        
        # De-list single-item lists to match xmltodict's behavior
        for tag, items in child_map.items():
            if len(items) == 1:
                result[tag] = items[0]
            else:
                result[tag] = items

    # Process text content
    text_nodes = [n for n in node.childNodes if _is_text_node(n)]
    if text_nodes:
        text = "".join(n.data for n in text_nodes).strip()
        if text:
            if result:
                # If there are attributes or children, text is a special key
                result['#text'] = text
            else:
                # Otherwise, the node's value is just the text
                return text
    
    # Return None for empty elements (e.g., <tag/>), otherwise the result dict
    return result if result else None

# ==============================================================================
# Internal helper functions for unparsing (dict -> ElementTree)
# ==============================================================================

def _build_node(parent, data):
    """
    Recursively build an ElementTree element from dictionary data.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key.startswith('@'):
                # Attribute
                parent.set(key[1:], str(value))
            elif key == '#text':
                # Text content
                parent.text = str(value)
            else:
                # Child element
                if isinstance(value, list):
                    # Handle repeated elements
                    for item in value:
                        child = ET.SubElement(parent, key)
                        _build_node(child, item)
                else:
                    # Handle single child element
                    child = ET.SubElement(parent, key)
                    _build_node(child, value)
    elif data is not None:
        # Simple text content for an element (e.g., <tag>value</tag>)
        parent.text = str(data)

# ==============================================================================
# Public API
# ==============================================================================

def parse(xml_input, **kwargs):
    """
    Parse an XML string into a Python dictionary.

    This function is designed to be API-compatible with the core functionality
    of `xmltodict.parse`.

    Args:
        xml_input (str or bytes): The XML string or bytes to parse.
        **kwargs: Additional arguments, ignored for compatibility.

    Returns:
        dict: A dictionary representing the XML structure.
    """
    dom = minidom.parseString(xml_input)
    root = dom.documentElement
    return {root.tagName: _parse_node(root)}

def unparse(input_dict, **kwargs):
    """
    Convert a Python dictionary into an XML string.

    This function is designed to be API-compatible with the core functionality
    of `xmltodict.unparse`.

    Args:
        input_dict (dict): The dictionary to convert. It must have a single
                           key representing the root element.
        **kwargs: Additional arguments, ignored for compatibility.

    Returns:
        str: The resulting XML string.
    
    Raises:
        TypeError: If input_dict is not a dictionary.
        ValueError: If input_dict does not have exactly one root element.
    """
    if not isinstance(input_dict, dict):
        raise TypeError("Input must be a dictionary.")
    if len(input_dict) != 1:
        raise ValueError("Input dictionary must have a single root element.")

    root_tag = list(input_dict.keys())[0]
    root_data = input_dict[root_tag]
    
    root = ET.Element(root_tag)
    _build_node(root, root_data)
    
    # ET.tostring returns bytes, so decode to a standard unicode string
    return ET.tostring(root, encoding='unicode')