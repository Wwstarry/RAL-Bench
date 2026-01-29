"""
Pure Python XML parsing and serialization library compatible with xmltodict API.
"""

import re
import sys
from collections import OrderedDict
from xml.parsers.expat import ParserCreate, ExpatError
from typing import Any, Dict, List, Optional, Union, Callable

# Type aliases
XMLDict = Dict[str, Any]
XMLList = List[XMLDict]

# Constants
ATTR_PREFIX = '@'
TEXT_KEY = '#text'
NAMESPACE_SEP = ':'
CDATA_SECTION = '<![CDATA['
CDATA_END = ']]>'

# Default settings
DEFAULT_ITEM_FUNC = lambda key, value: value
DEFAULT_ATTR_FUNC = lambda key, value: value
DEFAULT_CDATA_FUNC = lambda data: data
DEFAULT_PRECOMPUTED = False
DEFAULT_DICT_CLASS = OrderedDict
DEFAULT_LIST = list
DEFAULT_STRIP_WHITESPACE = True
DEFAULT_NAMESPACE_SEPARATOR = NAMESPACE_SEPARATOR
DEFAULT_DISABLE_ENTITIES = True
DEFAULT_PROCESS_NAMESPACES = False
DEFAULT_NAMESPACE_PREFIXES = {}

# For Python 2/3 compatibility
try:
    unicode
except NameError:
    unicode = str

try:
    basestring
except NameError:
    basestring = str


class ParsingInterrupted(Exception):
    """Exception raised when parsing is interrupted."""
    pass


class _DictSAXHandler:
    """SAX handler that builds dictionaries from XML events."""
    
    def __init__(self,
                 item_depth=0,
                 item_callback=DEFAULT_ITEM_FUNC,
                 attr_prefix=ATTR_PREFIX,
                 cdata_key=TEXT_KEY,
                 force_cdata=False,
                 cdata_separator='',
                 postprocessor=None,
                 dict_constructor=DEFAULT_DICT_CLASS,
                 strip_whitespace=DEFAULT_STRIP_WHITESPACE,
                 namespace_separator=DEFAULT_NAMESPACE_SEPARATOR,
                 namespaces=None,
                 force_list=None,
                 comment_key=None,
                 encoding='utf-8',
                 expat=None,
                 process_namespaces=DEFAULT_PROCESS_NAMESPACES,
                 disable_entities=DEFAULT_DISABLE_ENTITIES):
        
        self.path = []
        self.stack = []
        self.data = []
        self.item = None
        self.item_depth = item_depth
        self.item_callback = item_callback
        self.attr_prefix = attr_prefix
        self.cdata_key = cdata_key
        self.force_cdata = force_cdata
        self.cdata_separator = cdata_separator
        self.postprocessor = postprocessor
        self.dict_constructor = dict_constructor
        self.strip_whitespace = strip_whitespace
        self.namespace_separator = namespace_separator
        self.namespaces = namespaces or {}
        self.force_list = force_list or ()
        self.comment_key = comment_key
        self.encoding = encoding
        self.expat = expat
        self.process_namespaces = process_namespaces
        self.disable_entities = disable_entities
        
    def _build_name(self, name):
        """Build element name with namespace handling."""
        if self.process_namespaces and ':' in name:
            prefix, local = name.split(':', 1)
            if prefix in self.namespaces:
                return self.namespaces[prefix] + self.namespace_separator + local
        return name
    
    def _attrs(self, attrs):
        """Process attributes."""
        if attrs:
            return self.dict_constructor(
                (self.attr_prefix + self._build_name(k), v)
                for k, v in attrs.items()
            )
        return self.dict_constructor()
    
    def startElement(self, name, attrs):
        """Handle element start."""
        name = self._build_name(name)
        
        # Collect any pending text data
        self._flush_data()
        
        # Create new element
        d = self.dict_constructor()
        d.update(self._attrs(attrs))
        
        if self.stack:
            parent = self.stack[-1]
            if name in parent:
                # Handle repeated elements
                value = parent[name]
                if not isinstance(value, list):
                    parent[name] = [value, d]
                else:
                    value.append(d)
            else:
                parent[name] = d
        else:
            self.item = d
        
        self.stack.append(d)
        self.path.append(name)
    
    def endElement(self, name):
        """Handle element end."""
        name = self._build_name(name)
        
        # Flush any pending text data
        self._flush_data()
        
        # Remove from stack
        if self.stack:
            self.stack.pop()
        self.path.pop()
        
        # Apply item callback if at the right depth
        if self.item_depth == len(self.path):
            self.item = self.item_callback(self.path[-1] if self.path else None, self.item)
    
    def characters(self, data):
        """Handle character data."""
        self.data.append(data)
    
    def _flush_data(self):
        """Flush accumulated character data."""
        if self.data:
            data = ''.join(self.data)
            if self.strip_whitespace:
                data = data.strip()
            
            if data:
                if self.stack:
                    current = self.stack[-1]
                    if self.cdata_key in current:
                        # Append to existing text
                        current[self.cdata_key] += self.cdata_separator + data
                    else:
                        # Set new text
                        current[self.cdata_key] = data
            
            self.data = []
    
    def parseXml(self, xml_input):
        """Parse XML input."""
        if self.disable_entities and self.expat:
            try:
                self.expat.SetParamEntityParsing(self.expat.XML_PARAM_ENTITY_PARSING_NEVER)
            except AttributeError:
                # Python 2 doesn't have this method
                pass
        
        try:
            self.expat.Parse(xml_input, True)
        except ExpatError as e:
            raise ValueError("Malformed XML: " + str(e))
        
        self._flush_data()
        
        if self.postprocessor:
            return self.postprocessor(self.path, self.item)
        
        return self.item


def parse(xml_input,
          encoding='utf-8',
          expat=ParserCreate(),
          process_namespaces=False,
          namespace_separator=':',
          disable_entities=True,
          **kwargs):
    """
    Parse the given XML input and convert it into a dictionary.
    
    Args:
        xml_input: XML string or file-like object
        encoding: Input encoding
        expat: Expat parser instance
        process_namespaces: Whether to process namespaces
        namespace_separator: Separator for namespace prefixes
        disable_entities: Whether to disable entity parsing
        **kwargs: Additional parsing options
    
    Returns:
        Dictionary representation of the XML
    """
    # Handle file-like objects
    if hasattr(xml_input, 'read'):
        xml_input = xml_input.read()
    
    # Ensure string type
    if isinstance(xml_input, bytes):
        xml_input = xml_input.decode(encoding)
    
    # Create handler
    handler = _DictSAXHandler(
        encoding=encoding,
        expat=expat,
        process_namespaces=process_namespaces,
        namespace_separator=namespace_separator,
        disable_entities=disable_entities,
        **kwargs
    )
    
    # Configure expat parser
    expat.buffer_text = True
    expat.returns_unicode = False
    expat.StartElementHandler = handler.startElement
    expat.EndElementHandler = handler.endElement
    expat.CharacterDataHandler = handler.characters
    
    # Parse XML
    return handler.parseXml(xml_input)


def _escape_cdata(text):
    """Escape CDATA sections."""
    if CDATA_SECTION in text:
        # Split by CDATA sections and escape each part
        parts = text.split(CDATA_SECTION)
        result = []
        for i, part in enumerate(parts):
            if i > 0:
                # This part started with CDATA, find the end
                if CDATA_END in part:
                    cdata, rest = part.split(CDATA_END, 1)
                    result.append(CDATA_SECTION + cdata + CDATA_END)
                    result.append(_escape(rest))
                else:
                    # No end, treat as regular text
                    result.append(_escape(CDATA_SECTION + part))
            else:
                result.append(_escape(part))
        return ''.join(result)
    return _escape(text)


def _escape(text):
    """Escape XML special characters."""
    if not isinstance(text, basestring):
        text = str(text)
    
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    return text


def _is_string(value):
    """Check if value is a string."""
    return isinstance(value, basestring)


def _sorted_items(dict_obj):
    """Get sorted items from dictionary."""
    if hasattr(dict_obj, 'items'):
        items = dict_obj.items()
        try:
            return sorted(items)
        except TypeError:
            # Can't sort, return as-is
            return items
    return []


def _emit(key, value, content_handler,
          attr_prefix='@',
          cdata_key='#text',
          indent='',
          newl='',
          namespace_separator=':',
          full_document=True,
          pretty=True,
          depth=0):
    """Emit XML for a key-value pair."""
    
    # Calculate indentation
    if pretty and indent:
        indent_str = indent * depth
        newl_str = newl
    else:
        indent_str = ''
        newl_str = ''
    
    # Handle attributes
    if attr_prefix and key.startswith(attr_prefix):
        # This is an attribute
        attr_name = key[len(attr_prefix):]
        content_handler.startAttribute(attr_name)
        content_handler.characters(str(value))
        content_handler.endAttribute()
        return
    
    # Handle text content
    if key == cdata_key:
        if isinstance(value, dict):
            # Nested structure with text
            for k, v in _sorted_items(value):
                _emit(k, v, content_handler, attr_prefix, cdata_key,
                      indent, newl, namespace_separator, False, pretty, depth)
        else:
            # Plain text
            content_handler.characters(_escape_cdata(str(value)))
        return
    
    # Handle comments
    if key.startswith('#'):
        # Skip processing instructions and comments for now
        return
    
    # Handle regular elements
    content_handler.startElement(key, {})
    
    if isinstance(value, dict):
        # Dictionary value
        # First emit attributes
        for k, v in _sorted_items(value):
            if k.startswith(attr_prefix):
                _emit(k, v, content_handler, attr_prefix, cdata_key,
                      indent, newl, namespace_separator, False, pretty, depth)
        
        # Then emit other content
        for k, v in _sorted_items(value):
            if not k.startswith(attr_prefix) and k != cdata_key:
                _emit(k, v, content_handler, attr_prefix, cdata_key,
                      indent, newl, namespace_separator, False, pretty, depth + 1)
        
        # Handle text content if present
        if cdata_key in value:
            _emit(cdata_key, value[cdata_key], content_handler, attr_prefix, cdata_key,
                  indent, newl, namespace_separator, False, pretty, depth + 1)
    
    elif isinstance(value, list):
        # List value
        for item in value:
            _emit(key, item, content_handler, attr_prefix, cdata_key,
                  indent, newl, namespace_separator, False, pretty, depth + 1)
    
    else:
        # Simple value
        content_handler.characters(_escape_cdata(str(value)))
    
    content_handler.endElement(key)


class _DictToXMLHandler:
    """Content handler for converting dictionaries to XML."""
    
    def __init__(self, out=None, encoding='utf-8'):
        self.out = out
        self.encoding = encoding
        self._data = []
        self._in_attribute = False
    
    def write(self, data):
        """Write data to output."""
        if self.out is None:
            self._data.append(data)
        else:
            self.out.write(data)
    
    def startDocument(self):
        """Start document."""
        self.write('<?xml version="1.0" encoding="%s"?>' % self.encoding)
    
    def endDocument(self):
        """End document."""
        pass
    
    def startElement(self, name, attrs):
        """Start element."""
        self.write('<' + name)
        if attrs:
            for attr_name, attr_value in sorted(attrs.items()):
                self.write(' %s="%s"' % (attr_name, _escape(attr_value)))
        self.write('>')
    
    def endElement(self, name):
        """End element."""
        self.write('</%s>' % name)
    
    def characters(self, content):
        """Write character data."""
        self.write(content)
    
    def startAttribute(self, name):
        """Start attribute (internal use)."""
        self._in_attribute = True
        self.write(' %s="' % name)
    
    def endAttribute(self):
        """End attribute (internal use)."""
        self.write('"')
        self._in_attribute = False
    
    def getvalue(self):
        """Get string value if no output stream was provided."""
        if self.out is None:
            return ''.join(self._data)
        return None


def unparse(input_dict,
            output=None,
            encoding='utf-8',
            full_document=True,
            short_empty_elements=False,
            **kwargs):
    """
    Convert a dictionary to XML.
    
    Args:
        input_dict: Dictionary to convert
        output: Output file or stream
        encoding: Output encoding
        full_document: Whether to include XML declaration
        short_empty_elements: Whether to use short form for empty elements
        **kwargs: Additional formatting options
    
    Returns:
        XML string if no output specified, otherwise None
    """
    if not input_dict:
        raise ValueError("Input dictionary is empty")
    
    # Create content handler
    handler = _DictToXMLHandler(output, encoding)
    
    # Start document
    if full_document:
        handler.startDocument()
    
    # Get root key
    if len(input_dict) != 1:
        raise ValueError("Document must have exactly one root element")
    
    root_key = list(input_dict.keys())[0]
    root_value = input_dict[root_key]
    
    # Emit XML
    _emit(root_key, root_value, handler,
          full_document=full_document,
          **kwargs)
    
    # Return value if no output stream
    if output is None:
        return handler.getvalue()


# Convenience function aliases
parse = parse
unparse = unparse