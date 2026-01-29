"""
Pure Python XML parsing and serialization library compatible with xmltodict API.
"""

import re
import sys
from xml.parsers import expat
from collections import OrderedDict
from io import StringIO

# Python 2/3 compatibility
try:
    unicode
except NameError:
    unicode = str
    basestring = str

def parse(xml_input, encoding=None, expat=expat, process_namespaces=False,
          namespace_separator=':', disable_entities=True, **kwargs):
    """
    Parse the given XML input and convert it into a dictionary.
    
    :param xml_input: XML string or file-like object
    :param encoding: XML encoding (default: autodetect)
    :param expat: expat parser to use
    :param process_namespaces: whether to process namespaces
    :param namespace_separator: namespace separator character
    :param disable_entities: whether to disable entity expansion
    :return: dictionary representation of XML
    """
    if isinstance(xml_input, basestring):
        xml_input = StringIO(xml_input)
    
    handler = _DictSAXHandler(
        process_namespaces=process_namespaces,
        namespace_separator=namespace_separator,
        **kwargs
    )
    
    parser = expat.ParserCreate(encoding, namespace_separator if process_namespaces else '')
    
    if disable_entities:
        try:
            # Disable entity expansion to prevent XML bomb attacks
            parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
        except AttributeError:
            # Python 2.6 and earlier don't have this method
            pass
    
    parser.StartElementHandler = handler.start_element
    parser.EndElementHandler = handler.end_element
    parser.CharacterDataHandler = handler.characters
    
    parser.ParseFile(xml_input)
    
    return handler.result

def unparse(input_dict, output=None, encoding='utf-8', short_empty_elements=False, **kwargs):
    """
    Convert a dictionary back into XML.
    
    :param input_dict: dictionary to convert
    :param output: file-like object to write to (default: return string)
    :param encoding: output encoding
    :param short_empty_elements: use short form for empty elements
    :return: XML string if no output specified, otherwise None
    """
    if output is None:
        output = StringIO()
        _dict_to_xml(input_dict, output, encoding, short_empty_elements, **kwargs)
        return output.getvalue()
    else:
        _dict_to_xml(input_dict, output, encoding, short_empty_elements, **kwargs)
        return None

class _DictSAXHandler(object):
    """SAX handler that builds a dictionary from XML events."""
    
    def __init__(self, process_namespaces=False, namespace_separator=':', **kwargs):
        self.process_namespaces = process_namespaces
        self.namespace_separator = namespace_separator
        self.stack = []
        self.current = None
        self.result = None
        self.chars = []
    
    def start_element(self, name, attrs):
        # Process namespaces if requested
        if self.process_namespaces:
            name = name.replace(self.namespace_separator, ':')
        
        # Create new element
        element = OrderedDict()
        
        # Add attributes if any
        if attrs:
            for attr_name, attr_value in attrs.items():
                if self.process_namespaces:
                    attr_name = attr_name.replace(self.namespace_separator, ':')
                element['@' + attr_name] = attr_value
        
        # Push current element onto stack
        if self.current is not None:
            self.stack.append(self.current)
        
        self.current = element
        self.chars = []
    
    def end_element(self, name):
        # Process namespaces if requested
        if self.process_namespaces:
            name = name.replace(self.namespace_separator, ':')
        
        # Collect character data
        text = ''.join(self.chars).strip()
        if text:
            if '#text' in self.current:
                # If there's already text, append to it
                if isinstance(self.current['#text'], list):
                    self.current['#text'].append(text)
                else:
                    self.current['#text'] = [self.current['#text'], text]
            else:
                self.current['#text'] = text
        
        # Clear character buffer
        self.chars = []
        
        # Pop from stack or set as result
        if self.stack:
            parent = self.stack.pop()
            
            # Handle repeated elements by converting to list
            if name in parent:
                existing = parent[name]
                if isinstance(existing, list):
                    existing.append(self.current)
                else:
                    parent[name] = [existing, self.current]
            else:
                parent[name] = self.current
            
            self.current = parent
        else:
            self.result = {name: self.current}
            self.current = None
    
    def characters(self, data):
        self.chars.append(data)

def _dict_to_xml(d, output, encoding, short_empty_elements, indent="", **kwargs):
    """Recursively convert dictionary to XML."""
    if not d:
        return
    
    for key, value in d.items():
        if key.startswith('@'):
            continue  # Attributes are handled separately
        
        if key == '#text':
            # Text content - escape and write
            text = _escape_xml(str(value))
            output.write(text)
            continue
        
        # Write opening tag
        output.write(indent + '<' + key)
        
        # Write attributes
        attrs = OrderedDict()
        for k, v in d.items():
            if k.startswith('@'):
                attr_name = k[1:]
                attrs[attr_name] = v
        
        for attr_name, attr_value in attrs.items():
            output.write(' {}="{}"'.format(attr_name, _escape_xml(str(attr_value))))
        
        # Handle different value types
        if value is None or (isinstance(value, (dict, OrderedDict)) and not value):
            # Empty element
            if short_empty_elements:
                output.write('/>')
            else:
                output.write('></' + key + '>')
        else:
            output.write('>')
            
            if isinstance(value, (dict, OrderedDict)):
                # Nested element
                output.write('\n')
                _dict_to_xml(value, output, encoding, short_empty_elements, indent + "  ", **kwargs)
                output.write(indent)
            elif isinstance(value, list):
                # List of elements
                output.write('\n')
                for item in value:
                    _dict_to_xml({key: item}, output, encoding, short_empty_elements, indent + "  ", **kwargs)
                output.write(indent)
            else:
                # Simple text content
                _dict_to_xml(value, output, encoding, short_empty_elements, "", **kwargs)
            
            # Write closing tag
            output.write('</' + key + '>')
        
        output.write('\n')

def _escape_xml(text):
    """Escape XML special characters."""
    if not text:
        return text
    
    escapes = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&apos;'
    }
    
    # Fast path for strings without special characters
    if not any(c in text for c in escapes):
        return text
    
    # Replace special characters
    for char, replacement in escapes.items():
        text = text.replace(char, replacement)
    
    return text

# Maintain compatibility with original xmltodict
if __name__ == '__main__':
    # Simple test
    xml_string = '<root><item id="1">Text</item><item id="2">More text</item></root>'
    parsed = parse(xml_string)
    print("Parsed:", parsed)
    
    unparsed = unparse(parsed)
    print("Unparsed:", unparsed)