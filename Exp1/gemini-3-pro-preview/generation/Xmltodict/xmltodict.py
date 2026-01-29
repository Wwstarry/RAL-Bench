#!/usr/bin/env python
"Simple XML to Python dictionary parser and serializer"

try:
    from xml.parsers import expat
except ImportError:
    from xml.parsers import pyexpat as expat

import io

def parse(xml_input, encoding=None, expat=expat, process_namespaces=False, namespace_separator=':', **kwargs):
    """
    Parse the given XML input and convert it into a dictionary.

    :param xml_input: An XML string or a file-like object.
    :param encoding: The encoding of the XML input.
    :param expat: The expat module to use.
    :param process_namespaces: Whether to process namespaces.
    :param namespace_separator: Separator for namespaces.
    """
    parser = expat.ParserCreate(
        encoding,
        namespace_separator if process_namespaces else None
    )
    
    # Use a list as a stack. The first element is a container for the root.
    # We use a list for the container to allow multiple roots (though XML usually has one).
    # The result is a dict containing the root tag(s).
    result = {}
    stack = [result]

    def start(name, attrs):
        element = {}
        for key, value in attrs.items():
            element['@' + key] = value
            
        parent = stack[-1]
        
        # Add to parent
        if name in parent:
            existing = parent[name]
            if isinstance(existing, list):
                existing.append(element)
            else:
                parent[name] = [existing, element]
        else:
            parent[name] = element
            
        stack.append(element)

    def end(name):
        element = stack.pop()
        
        # Simplify the element if possible
        keys = element.keys()
        has_attrs = any(k.startswith('@') for k in keys)
        has_text = '#text' in keys
        has_children = any(not k.startswith('@') and k != '#text' for k in keys)
        
        value = element
        
        if not has_attrs and not has_children:
            if has_text:
                value = element['#text']
            else:
                value = None
        
        # If we simplified, we need to update the reference in the parent
        if value is not element:
            parent = stack[-1]
            existing = parent[name]
            if isinstance(existing, list):
                # The element we just finished is the last one in the list
                existing[-1] = value
            else:
                parent[name] = value

    def cdata(data):
        if len(stack) > 1:
            element = stack[-1]
            if '#text' in element:
                element['#text'] += data
            else:
                element['#text'] = data

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = cdata
    
    if hasattr(xml_input, 'read'):
        parser.ParseFile(xml_input)
    else:
        parser.Parse(xml_input, True)
        
    return result

class _Unparser(object):
    def __init__(self, output, encoding, full_document, short_empty_elements, **kwargs):
        self.output = output
        self.encoding = encoding
        self.full_document = full_document
        self.short_empty_elements = short_empty_elements

    def write(self, data):
        self.output.write(data)

    def escape(self, data):
        return data.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

    def unparse_node(self, name, value):
        if isinstance(value, list):
            for item in value:
                self.unparse_node(name, item)
            return

        if value is None:
            self.write('<' + name)
            if self.short_empty_elements:
                self.write(' />')
            else:
                self.write('></' + name + '>')
            return

        if isinstance(value, dict):
            self.write('<' + name)
            # Attributes
            for k, v in value.items():
                if k.startswith('@'):
                    self.write(' %s="%s"' % (k[1:], self.escape(str(v))))
            
            # Determine content
            has_children = False
            text_content = None
            
            children_keys = []
            for k in value.keys():
                if k.startswith('@'): continue
                if k == '#text':
                    text_content = value[k]
                    continue
                children_keys.append(k)
                has_children = True
            
            if has_children or text_content is not None:
                self.write('>')
                if text_content is not None:
                    self.write(self.escape(str(text_content)))
                for k in children_keys:
                    self.unparse_node(k, value[k])
                self.write('</' + name + '>')
            else:
                if self.short_empty_elements:
                    self.write(' />')
                else:
                    self.write('></' + name + '>')
            return

        # Scalar value
        self.write('<' + name + '>')
        self.write(self.escape(str(value)))
        self.write('</' + name + '>')

    def run(self, data):
        if self.full_document:
            self.write('<?xml version="1.0" encoding="%s"?>\n' % self.encoding)
        
        for key, value in data.items():
            self.unparse_node(key, value)

def unparse(input_dict, output=None, encoding='utf-8', full_document=True, short_empty_elements=False, **kwargs):
    """
    Emit an XML document for the given input dictionary.

    :param input_dict: The dictionary to convert to XML.
    :param output: A file-like object to write to. If None, returns a string.
    :param encoding: The encoding to use for the XML declaration.
    :param full_document: Whether to add the XML declaration.
    :param short_empty_elements: Whether to use self-closing tags for empty elements.
    """
    if output is None:
        is_string = True
        output = io.StringIO()
    else:
        is_string = False
    
    unparser = _Unparser(output, encoding, full_document, short_empty_elements, **kwargs)
    unparser.run(input_dict)
    
    if is_string:
        return output.getvalue()