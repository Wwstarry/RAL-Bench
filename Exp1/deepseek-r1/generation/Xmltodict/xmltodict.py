import re
import sys
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Union, TextIO
from xml.etree import ElementTree as ET

__all__ = ['parse', 'unparse']

# Type aliases
XMLDict = Dict[str, Any]
XMLList = List[XMLDict]

def parse(
    xml_input: Union[str, bytes, TextIO],
    encoding: Optional[str] = None,
    expat: Any = None,
    process_namespaces: bool = False,
    namespace_separator: str = ':',
    disable_entities: bool = True,
    force_list: Optional[List[str]] = None,
    force_cdata: bool = False,
    postprocessor: Any = None,
    **kwargs: Any
) -> XMLDict:
    """
    Parse XML document to Python dictionary.
    
    Args:
        xml_input: XML string, bytes, or file-like object
        encoding: Input encoding (for bytes)
        expat: Ignored (for API compatibility)
        process_namespaces: Whether to process namespace prefixes
        namespace_separator: Separator for namespace prefixes
        disable_entities: Whether to disable entity expansion
        force_list: List of element names to always treat as lists
        force_cdata: Whether to wrap text in CDATA sections
        postprocessor: Function to post-process elements
        **kwargs: Additional arguments (ignored)
    
    Returns:
        Dictionary representation of XML
    """
    if force_list is None:
        force_list = []
    
    # Handle input types
    if isinstance(xml_input, bytes):
        xml_string = xml_input.decode(encoding or 'utf-8')
    elif hasattr(xml_input, 'read'):
        xml_string = xml_input.read()
    else:
        xml_string = xml_input
    
    # Parse XML
    if disable_entities:
        # Simple entity replacement for common entities
        entity_map = {
            '&lt;': '<',
            '&gt;': '>',
            '&amp;': '&',
            '&quot;': '"',
            '&apos;': "'"
        }
        for entity, replacement in entity_map.items():
            xml_string = xml_string.replace(entity, replacement)
    
    root = ET.fromstring(xml_string)
    
    # Convert to dictionary
    return _element_to_dict(
        root,
        process_namespaces,
        namespace_separator,
        force_list,
        postprocessor
    )

def _element_to_dict(
    element: ET.Element,
    process_namespaces: bool,
    namespace_separator: str,
    force_list: List[str],
    postprocessor: Any
) -> Union[XMLDict, str]:
    """Convert XML element to dictionary."""
    
    # Handle tag name
    tag = element.tag
    if process_namespaces and '}' in tag:
        # Extract namespace and local name
        namespace_match = re.match(r'\{.*?\}', tag)
        if namespace_match:
            namespace = namespace_match.group(0)[1:-1]
            local_name = tag[namespace_match.end():]
            tag = f"{namespace}{namespace_separator}{local_name}"
    
    # Start with attributes
    result: XMLDict = {}
    if element.attrib:
        for key, value in element.attrib.items():
            attr_key = f"@{key}"
            if process_namespaces and '}' in key:
                namespace_match = re.match(r'\{.*?\}', key)
                if namespace_match:
                    namespace = namespace_match.group(0)[1:-1]
                    local_name = key[namespace_match.end():]
                    attr_key = f"@{namespace}{namespace_separator}{local_name}"
            result[attr_key] = value
    
    # Handle children
    children_by_tag: Dict[str, List[Any]] = {}
    text_parts: List[str] = []
    
    for child in element:
        if isinstance(child, ET.Element):
            child_dict = _element_to_dict(
                child,
                process_namespaces,
                namespace_separator,
                force_list,
                postprocessor
            )
            
            child_tag = child.tag
            if process_namespaces and '}' in child_tag:
                namespace_match = re.match(r'\{.*?\}', child_tag)
                if namespace_match:
                    namespace = namespace_match.group(0)[1:-1]
                    local_name = child_tag[namespace_match.end():]
                    child_tag = f"{namespace}{namespace_separator}{local_name}"
            
            if child_tag not in children_by_tag:
                children_by_tag[child_tag] = []
            children_by_tag[child_tag].append(child_dict)
        elif child.tail:
            text_parts.append(child.tail)
    
    # Add children to result
    for child_tag, children in children_by_tag.items():
        if len(children) == 1 and child_tag not in force_list:
            result[child_tag] = children[0]
        else:
            result[child_tag] = children
    
    # Handle text
    if element.text and element.text.strip():
        text = element.text.strip()
        if text_parts:
            text = text + ''.join(text_parts)
        
        if '#text' in result:
            if isinstance(result['#text'], list):
                result['#text'].append(text)
            else:
                result['#text'] = [result['#text'], text]
        else:
            result['#text'] = text
    
    # Apply postprocessor
    if postprocessor:
        result = postprocessor(tag, result)
    
    # If no attributes and only text, return just the text
    if len(result) == 1 and '#text' in result:
        return result['#text']
    
    return result

def unparse(
    input_dict: XMLDict,
    output: Optional[Union[str, TextIO]] = None,
    encoding: str = 'utf-8',
    short_empty_elements: bool = False,
    pretty: bool = False,
    indent: str = '  ',
    **kwargs: Any
) -> Optional[str]:
    """
    Convert Python dictionary to XML document.
    
    Args:
        input_dict: Dictionary to convert
        output: Output file or None to return string
        encoding: Output encoding
        short_empty_elements: Use short form for empty elements
        pretty: Pretty-print output
        indent: Indentation string
        **kwargs: Additional arguments (ignored)
    
    Returns:
        XML string if output is None, otherwise None
    """
    # Create root element
    if not isinstance(input_dict, dict) or len(input_dict) != 1:
        raise ValueError("Input dict must have exactly one root key")
    
    root_tag = next(iter(input_dict))
    root_value = input_dict[root_tag]
    
    root = ET.Element(root_tag)
    _dict_to_element(root_value, root, short_empty_elements)
    
    # Convert to string
    if hasattr(ET, 'indent') and pretty:
        ET.indent(root, space=indent)
    
    xml_string = ET.tostring(
        root,
        encoding=encoding,
        method='xml',
        short_empty_elements=short_empty_elements
    ).decode(encoding)
    
    # Write output
    if output is None:
        return xml_string
    elif isinstance(output, str):
        with open(output, 'w', encoding=encoding) as f:
            f.write(xml_string)
    else:
        output.write(xml_string)
    
    return None

def _dict_to_element(
    data: Any,
    parent: ET.Element,
    short_empty_elements: bool
) -> None:
    """Convert dictionary data to XML elements."""
    
    if isinstance(data, dict):
        # Handle attributes and content
        text_content = None
        processed_keys = set()
        
        for key, value in data.items():
            if key == '#text':
                text_content = str(value)
                processed_keys.add(key)
            elif key.startswith('@'):
                attr_name = key[1:]
                parent.set(attr_name, str(value))
                processed_keys.add(key)
        
        # Handle remaining keys as child elements
        for key, value in data.items():
            if key in processed_keys:
                continue
            
            if isinstance(value, list):
                for item in value:
                    child = ET.SubElement(parent, key)
                    _dict_to_element(item, child, short_empty_elements)
            else:
                child = ET.SubElement(parent, key)
                _dict_to_element(value, child, short_empty_elements)
        
        # Set text content if present
        if text_content is not None:
            parent.text = text_content
            
    elif isinstance(data, list):
        # List at root level - each item becomes a sibling
        for item in data:
            _dict_to_element(item, parent, short_empty_elements)
    else:
        # Simple value becomes text content
        if data is not None:
            parent.text = str(data)

# For backward compatibility
def Parse(xml_input, *args, **kwargs):
    """Deprecated alias for parse."""
    import warnings
    warnings.warn(
        "Parse is deprecated, use parse instead",
        DeprecationWarning,
        stacklevel=2
    )
    return parse(xml_input, *args, **kwargs)

def Unparse(input_dict, *args, **kwargs):
    """Deprecated alias for unparse."""
    import warnings
    warnings.warn(
        "Unparse is deprecated, use unparse instead",
        DeprecationWarning,
        stacklevel=2
    )
    return unparse(input_dict, *args, **kwargs)