"""
Pure Python xmltodict-compatible implementation.

Implements:
    - xmltodict.parse(xml_string, ...)
    - xmltodict.unparse(mapping, ...)
"""

import re

# --- XML Parsing ---

def parse(xml_input, encoding=None, expat=None, process_namespaces=False, xml_attribs=False,
          attr_prefix='@', cdata_key='#text', dict_constructor=dict, strip_whitespace=True,
          postprocessor=None, force_list=None, **kwargs):
    """
    Parse XML string into Python dict.
    """
    if hasattr(xml_input, 'read'):
        xml_string = xml_input.read()
    else:
        xml_string = xml_input

    if encoding and isinstance(xml_string, bytes):
        xml_string = xml_string.decode(encoding)
    elif isinstance(xml_string, bytes):
        xml_string = xml_string.decode('utf-8')

    parser = _XMLDictParser(
        attr_prefix=attr_prefix,
        cdata_key=cdata_key,
        dict_constructor=dict_constructor,
        strip_whitespace=strip_whitespace,
        postprocessor=postprocessor,
        force_list=force_list or [],
        process_namespaces=process_namespaces,
        xml_attribs=xml_attribs,
    )
    return parser.parse(xml_string)

# --- XML Unparsing ---

def unparse(item, output=None, encoding='utf-8', full_document=True, short_empty_elements=False,
            attr_prefix='@', cdata_key='#text', pretty=False, indent="  ", newl="\n"):
    """
    Convert Python dict to XML string.
    """
    xml = _XMLDictUnparser(
        attr_prefix=attr_prefix,
        cdata_key=cdata_key,
        pretty=pretty,
        indent=indent,
        newl=newl,
        short_empty_elements=short_empty_elements,
    ).unparse(item, full_document=full_document)

    if output is not None:
        if hasattr(output, 'write'):
            if encoding:
                if isinstance(xml, str):
                    xml = xml.encode(encoding)
            output.write(xml)
            return None
        else:
            raise ValueError("output must be a file-like object")
    else:
        if encoding and isinstance(xml, str):
            return xml.encode(encoding)
        return xml

# --- Internal XML Parser ---

class _XMLDictParser:
    def __init__(self, attr_prefix='@', cdata_key='#text', dict_constructor=dict,
                 strip_whitespace=True, postprocessor=None, force_list=None,
                 process_namespaces=False, xml_attribs=False):
        self.attr_prefix = attr_prefix
        self.cdata_key = cdata_key
        self.dict_constructor = dict_constructor
        self.strip_whitespace = strip_whitespace
        self.postprocessor = postprocessor
        self.force_list = set(force_list or [])
        self.process_namespaces = process_namespaces
        self.xml_attribs = xml_attribs

    def parse(self, xml_string):
        # Remove XML declaration
        xml_string = re.sub(r'<\?xml[^>]*\?>', '', xml_string, flags=re.MULTILINE)
        xml_string = xml_string.strip()
        # Parse
        root, _ = self._parse_element(xml_string, 0)
        return root

    def _parse_element(self, s, i):
        # Find next tag
        tag_re = re.compile(r'<([^\s>/!]+)([^>]*)>|<!--.*?-->|<!\[CDATA\[(.*?)\]\]>|</([^\s>]+)>', re.DOTALL)
        text_re = re.compile(r'[^<]+')
        stack = []
        root = None
        pos = i
        while pos < len(s):
            m = tag_re.search(s, pos)
            if not m:
                # Only text left
                text_m = text_re.match(s, pos)
                if text_m:
                    text = text_m.group(0)
                    pos = text_m.end()
                    if self.strip_whitespace:
                        text = text.strip()
                    if text:
                        return text, pos
                break
            if m.start() > pos:
                # Text node before tag
                text = s[pos:m.start()]
                if self.strip_whitespace:
                    text = text.strip()
                if text:
                    return text, m.start()
            if m.group(1):
                # Start tag
                tag = m.group(1)
                attr_str = m.group(2)
                attrs = self._parse_attrs(attr_str)
                empty = attr_str.strip().endswith('/')
                pos = m.end()
                if empty:
                    node = self.dict_constructor()
                    if attrs:
                        node.update({self.attr_prefix + k: v for k, v in attrs.items()})
                    return {tag: node}, pos
                # Parse children
                children = []
                while True:
                    child, pos2 = self._parse_element(s, pos)
                    pos = pos2
                    if isinstance(child, dict):
                        children.append(child)
                    elif isinstance(child, str):
                        if child:
                            children.append(child)
                    # Find end tag
                    end_m = tag_re.match(s, pos)
                    if end_m and end_m.group(4) == tag:
                        pos = end_m.end()
                        break
                    elif end_m and end_m.group(1):
                        # Nested start tag
                        continue
                    elif end_m and end_m.group(3) is not None:
                        # CDATA
                        children.append(end_m.group(3))
                        pos = end_m.end()
                        continue
                    elif end_m and end_m.group(0).startswith('<!--'):
                        # Comment, skip
                        pos = end_m.end()
                        continue
                    else:
                        # Text node or whitespace
                        text_m = text_re.match(s, pos)
                        if text_m:
                            text = text_m.group(0)
                            pos = text_m.end()
                            if self.strip_whitespace:
                                text = text.strip()
                            if text:
                                children.append(text)
                        else:
                            break
                node = self.dict_constructor()
                if attrs:
                    node.update({self.attr_prefix + k: v for k, v in attrs.items()})
                # Merge children
                child_map = self.dict_constructor()
                texts = []
                for c in children:
                    if isinstance(c, dict):
                        for k, v in c.items():
                            if k in child_map:
                                if not isinstance(child_map[k], list):
                                    child_map[k] = [child_map[k]]
                                child_map[k].append(v)
                            else:
                                child_map[k] = v
                    else:
                        texts.append(c)
                if child_map:
                    node.update(child_map)
                if texts:
                    text_val = ''.join(texts)
                    if self.strip_whitespace:
                        text_val = text_val.strip()
                    if text_val:
                        node[self.cdata_key] = text_val
                return {tag: node}, pos
            elif m.group(3) is not None:
                # CDATA
                cdata = m.group(3)
                pos = m.end()
                return cdata, pos
            elif m.group(4):
                # End tag
                pos = m.end()
                return None, pos
            elif m.group(0).startswith('<!--'):
                # Comment, skip
                pos = m.end()
                continue
        return None, pos

    def _parse_attrs(self, attr_str):
        attr_re = re.compile(r'([^\s=]+)\s*=\s*(".*?"|\'.*?\')')
        attrs = {}
        for m in attr_re.finditer(attr_str):
            k = m.group(1)
            v = m.group(2)[1:-1]
            attrs[k] = v
        return attrs

# --- Internal XML Unparser ---

class _XMLDictUnparser:
    def __init__(self, attr_prefix='@', cdata_key='#text', pretty=False, indent="  ", newl="\n",
                 short_empty_elements=False):
        self.attr_prefix = attr_prefix
        self.cdata_key = cdata_key
        self.pretty = pretty
        self.indent = indent
        self.newl = newl
        self.short_empty_elements = short_empty_elements

    def unparse(self, obj, full_document=True):
        # obj is expected to be {root: ...}
        if not isinstance(obj, dict) or len(obj) != 1:
            raise ValueError("Root object must be a dict with a single key")
        root_tag = list(obj.keys())[0]
        root_val = obj[root_tag]
        xml = ''
        if full_document:
            xml += '<?xml version="1.0" encoding="UTF-8"?>'
            if self.pretty:
                xml += self.newl
        xml += self._to_xml(root_tag, root_val, level=0)
        return xml

    def _to_xml(self, tag, value, level=0):
        attrs = ''
        children = []
        text = None
        if isinstance(value, dict):
            for k, v in value.items():
                if k.startswith(self.attr_prefix):
                    attrs += ' %s="%s"' % (k[len(self.attr_prefix):], _escape(str(v)))
                elif k == self.cdata_key:
                    text = v
                else:
                    children.append((k, v))
        else:
            text = value
        xml = ''
        indent = self.indent * level if self.pretty else ''
        newl = self.newl if self.pretty else ''
        if isinstance(value, dict) and not children and text is None:
            # Empty tag with attributes only
            if self.short_empty_elements:
                xml += '%s<%s%s/>%s' % (indent, tag, attrs, newl)
            else:
                xml += '%s<%s%s></%s>%s' % (indent, tag, attrs, tag, newl)
        elif not children:
            # Leaf node
            if text is None:
                text = ''
            xml += '%s<%s%s>%s</%s>%s' % (indent, tag, attrs, _escape(str(text)), tag, newl)
        else:
            xml += '%s<%s%s>' % (indent, tag, attrs)
            if self.pretty and (children or text):
                xml += newl
            if text is not None:
                xml += (indent + self.indent if self.pretty else '') + _escape(str(text)) + (newl if self.pretty else '')
            for k, v in children:
                if isinstance(v, list):
                    for item in v:
                        xml += self._to_xml(k, item, level=level+1)
                else:
                    xml += self._to_xml(k, v, level=level+1)
            xml += '%s</%s>%s' % (indent, tag, newl)
        return xml

# --- XML Escaping ---

def _escape(text):
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))