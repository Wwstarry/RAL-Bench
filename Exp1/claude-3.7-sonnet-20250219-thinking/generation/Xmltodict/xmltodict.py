"""
xmltodict: Makes working with XML feel like working with JSON
===============================================================

This module provides a simple API to convert XML to Python dictionaries
and back again, preserving the structure and attributes of the original XML.
"""

from xml.parsers import expat
from xml.sax.saxutils import escape, quoteattr
import re
import sys
from collections import OrderedDict

try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping

try:
    from cStringIO import StringIO
except ImportError:
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO


def parse(xml_input, encoding=None, expat=expat, process_namespaces=False,
          namespace_separator=':', disable_entities=True,
          process_comments=False, **kwargs):
    """
    Parse the given XML input and convert it into a dictionary.

    Arguments:
    - xml_input: XML input as string or file-like object
    - encoding: Optional encoding
    - expat: XML parser (default is xml.parsers.expat)
    - process_namespaces: Process namespaces (default is False)
    - namespace_separator: Separator for namespaces (default is ':')
    - disable_entities: Disable entities (default is True)
    - process_comments: Process XML comments (default is False)
    """
    handler = _DictSAXHandler(
        namespace_separator=namespace_separator,
        process_namespaces=process_namespaces,
        process_comments=process_comments,
        **kwargs
    )

    if hasattr(xml_input, 'read'):
        # File-like object
        parser = expat.ParserCreate(
            encoding,
            namespace_separator if process_namespaces else None
        )
        parser.ordered_attributes = True
        parser.StartElementHandler = handler.start_element
        parser.EndElementHandler = handler.end_element
        parser.CharacterDataHandler = handler.char_data
        if process_comments:
            parser.CommentHandler = handler.comment
        if disable_entities:
            try:
                parser.UseForeignDTD(False)
            except AttributeError:
                pass
        parser.ParseFile(xml_input)
    else:
        # String
        parser = expat.ParserCreate(
            encoding,
            namespace_separator if process_namespaces else None
        )
        parser.ordered_attributes = True
        parser.StartElementHandler = handler.start_element
        parser.EndElementHandler = handler.end_element
        parser.CharacterDataHandler = handler.char_data
        if process_comments:
            parser.CommentHandler = handler.comment
        if disable_entities:
            try:
                parser.UseForeignDTD(False)
            except AttributeError:
                pass
        parser.Parse(xml_input)

    return handler.item


def unparse(input_dict, output=None, encoding='utf-8', full_document=True,
           pretty=False, indent="  ", newl="\n", short_empty_elements=False,
           **kwargs):
    """
    Convert a dictionary to an XML string.

    Arguments:
    - input_dict: Dictionary to convert to XML
    - output: Output stream (default is to return a string)
    - encoding: Output encoding (default is 'utf-8')
    - full_document: Include XML declaration (default is True)
    - pretty: Pretty-print the output (default is False)
    - indent: Indentation string (default is two spaces)
    - newl: Newline string (default is \n)
    - short_empty_elements: Use short empty elements (default is False)
    """
    if full_document and encoding is not None:
        if output:
            output.write('<?xml version="1.0" encoding="%s"?>%s' % 
                      (encoding, newl if pretty else ''))
        else:
            output_str = '<?xml version="1.0" encoding="%s"?>%s' % \
                      (encoding, newl if pretty else '')
    else:
        output_str = ''
    
    must_return = (output is None)
    output = output or StringIO()
    
    serializer = _XMLSerializer(
        output=output, 
        pretty=pretty,
        indent=indent, 
        newl=newl, 
        short_empty_elements=short_empty_elements,
        **kwargs
    )
    serializer.serialize(input_dict)
    
    if must_return:
        result = output.getvalue()
        if isinstance(result, bytes) and encoding:
            result = result.decode(encoding)
        return output_str + result
    

class _DictSAXHandler:
    def __init__(self, namespace_separator=':', process_namespaces=False,
                process_comments=False, item_depth=0, item_callback=None,
                attr_prefix='@', cdata_key='#text', force_cdata=False,
                cdata_separator='', postprocessor=None, dict_constructor=OrderedDict,
                strip_whitespace=True, namespace_declarations=True,
                force_list=None):
        self.path = []
        self.stack = []
        self.data = []
        self.item = None
        self.item_depth = item_depth
        self.process_namespaces = process_namespaces
        self.process_comments = process_comments
        self.namespace_separator = namespace_separator
        self.item_callback = item_callback
        self.attr_prefix = attr_prefix
        self.cdata_key = cdata_key
        self.force_cdata = force_cdata
        self.cdata_separator = cdata_separator
        self.postprocessor = postprocessor
        self.dict_constructor = dict_constructor
        self.strip_whitespace = strip_whitespace
        self.namespace_declarations = namespace_declarations
        self.force_list = force_list if force_list else set()

    def _build_name(self, full_name):
        if not self.process_namespaces:
            return full_name
        i = full_name.find(self.namespace_separator)
        if i == -1:
            return full_name
        namespace, name = full_name[:i], full_name[i+1:]
        return self.namespace_separator.join((namespace, name))

    def start_element(self, name, attrs):
        name = self._build_name(name)
        attrs = self.dict_constructor([(self._build_name(key), value)
                                      for key, value in attrs.items()])
        self.path.append((name, attrs))
        
        if len(self.path) > self.item_depth:
            self.stack.append((self.item, self.data))
            if self.item is None:
                self.item = self.dict_constructor()
            else:
                data = self.dict_constructor()
                if name not in self.item:
                    self.item[name] = data
                else:
                    if isinstance(self.item[name], list):
                        self.item[name].append(data)
                    else:
                        self.item[name] = [self.item[name], data]
                self.item = data
            self.data = []
        
        # Process attributes
        for key, value in attrs.items():
            if self.namespace_declarations and key.startswith('xmlns:'):
                continue
            self.item[self.attr_prefix + key] = value

    def end_element(self, name):
        name = self._build_name(name)
        
        if len(self.path) == self.item_depth:
            item = self.item
            self.item = None
            if self.item_callback:
                self.item_callback(item, name)
        else:
            data = ''.join(self.data)
            if self.strip_whitespace:
                data = data.strip() or ''
            if data and self.force_cdata and self.item is not None:
                self.item[self.cdata_key] = data
            elif self.item is not None:
                if data or self.force_cdata:
                    if self.cdata_key in self.item:
                        self.item[self.cdata_key] += self.cdata_separator + data
                    else:
                        self.item[self.cdata_key] = data
            
            if name in self.force_list:
                if name not in self.item:
                    self.item[name] = []
                elif not isinstance(self.item[name], list):
                    self.item[name] = [self.item[name]]
            
            item = self.item
            self.item, self.data = self.stack.pop()
            
            if self.postprocessor:
                item = self.postprocessor(self.path[-1][0], item)
            
            if item is not None and self.path[-1][0] != name:
                raise ValueError(f"End tag '{name}' does not match start tag '{self.path[-1][0]}'")
            
        self.path.pop()

    def char_data(self, data):
        if not self.data:
            self.data = [data]
        else:
            self.data.append(data)
    
    def comment(self, data):
        if self.process_comments:
            self.start_element('@comment', {})
            self.data.append(data)
            self.end_element('@comment')


class _XMLSerializer:
    def __init__(self, output, pretty=False, indent="  ", newl="\n",
                attr_prefix='@', cdata_key='#text', depth=0,
                preprocessor=None, full_document=True,
                short_empty_elements=False,
                **kwargs):
        self.output = output
        self.pretty = pretty
        self.indent = indent
        self.newl = newl
        self.attr_prefix = attr_prefix
        self.cdata_key = cdata_key
        self.depth = depth
        self.preprocessor = preprocessor
        self.full_document = full_document
        self.short_empty_elements = short_empty_elements
    
    def serialize(self, item):
        if self.preprocessor:
            item = self.preprocessor(item)
        
        if isinstance(item, dict):
            for key, value in item.items():
                if not key.startswith(self.attr_prefix) and key != self.cdata_key:
                    self._serialize_element(key, value)
        else:
            self._serialize_element('root', item)
    
    def _serialize_element(self, key, value):
        if isinstance(value, list):
            for v in value:
                self._serialize_element(key, v)
        else:
            if self.pretty:
                self.output.write(self.indent * self.depth)
            
            self.output.write('<' + key)
            
            if isinstance(value, dict):
                attrs = []
                children = []
                text = None
                
                for k, v in value.items():
                    if k.startswith(self.attr_prefix):
                        attrs.append((k[len(self.attr_prefix):], v))
                    elif k == self.cdata_key:
                        text = v
                    else:
                        children.append((k, v))
                
                # Write attributes
                for attr_key, attr_value in attrs:
                    self.output.write(' %s=%s' % (
                        attr_key, quoteattr(str(attr_value))))
                
                if not children and not text:
                    if self.short_empty_elements:
                        self.output.write('/>')
                        if self.pretty:
                            self.output.write(self.newl)
                    else:
                        self.output.write('></%s>' % key)
                        if self.pretty:
                            self.output.write(self.newl)
                else:
                    self.output.write('>')
                    
                    if text is not None:
                        self.output.write(escape(str(text)))
                    
                    if children:
                        if self.pretty:
                            self.output.write(self.newl)
                        
                        self.depth += 1
                        for child_key, child_value in children:
                            self._serialize_element(child_key, child_value)
                        self.depth -= 1
                        
                        if self.pretty:
                            self.output.write(self.indent * self.depth)
                    
                    self.output.write('</%s>' % key)
                    if self.pretty:
                        self.output.write(self.newl)
            else:
                # Simple value
                self.output.write('>')
                if value is not None:
                    self.output.write(escape(str(value)))
                self.output.write('</%s>' % key)
                if self.pretty:
                    self.output.write(self.newl)


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2:
        with open(sys.argv[1], 'r') as f:
            print(parse(f.read()))