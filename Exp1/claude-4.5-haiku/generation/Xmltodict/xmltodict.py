"""
Pure Python XML parsing and serialization library.
API-compatible with xmltodict.
"""

import xml.etree.ElementTree as ET
from collections import OrderedDict
from io import StringIO


def parse(xml_input, encoding=None, process_namespaces=False, namespace_separator=':', 
          strip_whitespace=True, force_list=None, force_cdata=False, attr_prefix='@',
          text_key='#text', cdata_key='#cdata', comment_key='#comment', 
          dict_constructor=OrderedDict, list_constructor=list, **kwargs):
    """
    Parse an XML string or file-like object into a nested dictionary.
    
    Args:
        xml_input: XML string or file-like object
        encoding: Encoding to use (default: auto-detect)
        process_namespaces: Whether to process namespaces (default: False)
        namespace_separator: Separator for namespace prefixes (default: ':')
        strip_whitespace: Whether to strip whitespace from text (default: True)
        force_list: List of element names that should always be lists
        force_cdata: Whether to force CDATA sections (default: False)
        attr_prefix: Prefix for attributes (default: '@')
        text_key: Key for text content (default: '#text')
        cdata_key: Key for CDATA content (default: '#cdata')
        comment_key: Key for comments (default: '#comment')
        dict_constructor: Constructor for dictionaries (default: OrderedDict)
        list_constructor: Constructor for lists (default: list)
    
    Returns:
        A nested dictionary representation of the XML.
    """
    if force_list is None:
        force_list = []
    
    if isinstance(xml_input, str):
        xml_string = xml_input
    else:
        xml_string = xml_input.read()
        if isinstance(xml_string, bytes):
            xml_string = xml_string.decode(encoding or 'utf-8')
    
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse XML: {e}")
    
    result = dict_constructor()
    root_name = root.tag
    root_dict = _element_to_dict(
        root, 
        process_namespaces=process_namespaces,
        namespace_separator=namespace_separator,
        strip_whitespace=strip_whitespace,
        force_list=force_list,
        attr_prefix=attr_prefix,
        text_key=text_key,
        cdata_key=cdata_key,
        comment_key=comment_key,
        dict_constructor=dict_constructor,
        list_constructor=list_constructor
    )
    result[root_name] = root_dict
    
    return result


def _element_to_dict(element, process_namespaces=False, namespace_separator=':',
                     strip_whitespace=True, force_list=None, attr_prefix='@',
                     text_key='#text', cdata_key='#cdata', comment_key='#comment',
                     dict_constructor=OrderedDict, list_constructor=list):
    """
    Convert an XML element to a dictionary.
    """
    if force_list is None:
        force_list = []
    
    result = dict_constructor()
    
    # Handle attributes
    if element.attrib:
        for key, value in element.attrib.items():
            attr_key = f"{attr_prefix}{key}"
            result[attr_key] = value
    
    # Handle child elements
    children = dict_constructor()
    for child in element:
        child_name = child.tag
        child_dict = _element_to_dict(
            child,
            process_namespaces=process_namespaces,
            namespace_separator=namespace_separator,
            strip_whitespace=strip_whitespace,
            force_list=force_list,
            attr_prefix=attr_prefix,
            text_key=text_key,
            cdata_key=cdata_key,
            comment_key=comment_key,
            dict_constructor=dict_constructor,
            list_constructor=list_constructor
        )
        
        if child_name in children:
            # Convert to list if not already
            if not isinstance(children[child_name], list):
                children[child_name] = list_constructor([children[child_name]])
            children[child_name].append(child_dict)
        else:
            if child_name in force_list:
                children[child_name] = list_constructor([child_dict])
            else:
                children[child_name] = child_dict
    
    result.update(children)
    
    # Handle text content
    text = element.text
    if text is not None:
        if strip_whitespace:
            text = text.strip()
        if text:
            if result:
                result[text_key] = text
            else:
                return text
    
    # If no children and no attributes, return text or None
    if not result:
        return None
    
    return result


def unparse(input_dict, output=None, encoding='utf-8', full_document=True,
            short_empty_elements=False, **kwargs):
    """
    Convert a nested dictionary back into an XML string.
    
    Args:
        input_dict: Dictionary representation of XML
        output: File-like object to write to (default: None, returns string)
        encoding: Encoding to use (default: 'utf-8')
        full_document: Whether to include XML declaration (default: True)
        short_empty_elements: Whether to use short empty element syntax (default: False)
    
    Returns:
        XML string if output is None, otherwise None.
    """
    if len(input_dict) != 1:
        raise ValueError("Dictionary must have exactly one root element")
    
    root_name = list(input_dict.keys())[0]
    root_value = input_dict[root_name]
    
    root_element = _dict_to_element(root_name, root_value, **kwargs)
    
    if output is None:
        # Return as string
        xml_string = ET.tostring(root_element, encoding='unicode', method='xml')
        if full_document:
            xml_string = f'<?xml version="1.0" encoding="{encoding}"?>\n{xml_string}'
        return xml_string
    else:
        # Write to file-like object
        tree = ET.ElementTree(root_element)
        if full_document:
            output.write(f'<?xml version="1.0" encoding="{encoding}"?>\n')
        tree.write(output, encoding=encoding, xml_declaration=False, method='xml')


def _dict_to_element(name, value, attr_prefix='@', text_key='#text', 
                     cdata_key='#cdata', comment_key='#comment', **kwargs):
    """
    Convert a dictionary entry to an XML element.
    """
    element = ET.Element(name)
    
    if value is None:
        return element
    
    if isinstance(value, str):
        element.text = value
        return element
    
    if isinstance(value, list):
        # This shouldn't happen at top level, but handle it
        raise ValueError(f"Cannot convert list to element directly")
    
    if isinstance(value, dict):
        # Separate attributes, text, and child elements
        text_content = None
        
        for key, val in value.items():
            if key.startswith(attr_prefix):
                # Attribute
                attr_name = key[len(attr_prefix):]
                element.set(attr_name, str(val))
            elif key == text_key:
                # Text content
                text_content = val
            elif key == cdata_key:
                # CDATA content
                text_content = val
            elif key == comment_key:
                # Comment - skip for now
                pass
            else:
                # Child element(s)
                if isinstance(val, list):
                    for item in val:
                        child = _dict_to_element(key, item, attr_prefix=attr_prefix,
                                                text_key=text_key, cdata_key=cdata_key,
                                                comment_key=comment_key, **kwargs)
                        element.append(child)
                else:
                    child = _dict_to_element(key, val, attr_prefix=attr_prefix,
                                            text_key=text_key, cdata_key=cdata_key,
                                            comment_key=comment_key, **kwargs)
                    element.append(child)
        
        if text_content is not None:
            element.text = str(text_content)
        
        return element
    
    # Primitive type
    element.text = str(value)
    return element