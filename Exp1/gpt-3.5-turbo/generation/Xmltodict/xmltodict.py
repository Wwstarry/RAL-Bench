"""
A pure Python XML parsing and serialization library compatible with the core parts
of the reference xmltodict project.

Provides:
- xmltodict.parse(xml_string, **kwargs)
- xmltodict.unparse(mapping, **kwargs)

Features:
- parse returns nested dicts with element names as keys,
  attributes under "@attr" keys,
  text content under "#text",
  repeated elements grouped into lists,
  namespace prefixes preserved in element names.
- unparse converts such dicts back into XML, preserving structure.
"""

from xml.parsers import expat

def parse(xml_input, encoding='utf-8', process_namespaces=False, **kwargs):
    """
    Parse an XML string or bytes into a nested dictionary.

    Parameters:
    - xml_input: XML string or bytes to parse.
    - encoding: encoding of the input if bytes.
    - process_namespaces: if True, namespace URIs are processed (not implemented here).
    - kwargs: ignored for compatibility.

    Returns:
    - dict representing the XML structure.
    """
    if isinstance(xml_input, bytes):
        xml_input = xml_input.decode(encoding)

    parser = expat.ParserCreate(namespace_separator=':')
    # Stack to hold elements: each item is (tag, attrs, children_dict)
    stack = []

    # The root element dict to return
    root = None

    # Current text buffer
    text_buffer = []

    def _flush_text():
        text = ''.join(text_buffer).strip()
        text_buffer.clear()
        return text if text else None

    def start_element(name, attrs):
        nonlocal stack
        # Flush text from previous element
        text = _flush_text()
        if stack:
            # If previous element has text, store it
            if text:
                parent = stack[-1][2]
                # If parent already has #text, append
                if '#text' in parent:
                    parent['#text'] += text
                else:
                    parent['#text'] = text

        # Prepare attributes dict with '@' prefix
        attr_dict = {}
        for k, v in attrs.items():
            attr_dict['@' + k] = v

        # New element dict: start with attributes if any
        elem_dict = {}
        if attr_dict:
            elem_dict.update(attr_dict)

        # Push new element on stack
        stack.append([name, elem_dict, {}])  # name, attributes+text dict, children dict

    def end_element(name):
        nonlocal stack, root
        # Flush text for this element
        text = _flush_text()
        name_, attr_text_dict, children = stack.pop()
        assert name == name_

        # If text exists, add it
        if text:
            if '#text' in attr_text_dict:
                attr_text_dict['#text'] += text
            else:
                attr_text_dict['#text'] = text

        # Merge children into attr_text_dict
        for k, v in children.items():
            if k in attr_text_dict:
                # If key exists, convert to list or append
                if isinstance(attr_text_dict[k], list):
                    attr_text_dict[k].append(v)
                else:
                    attr_text_dict[k] = [attr_text_dict[k], v]
            else:
                attr_text_dict[k] = v

        # Now attr_text_dict represents this element's dict

        if stack:
            # Add this element to parent's children dict
            parent_children = stack[-1][2]
            if name in parent_children:
                # Already exists, convert to list or append
                if isinstance(parent_children[name], list):
                    parent_children[name].append(attr_text_dict)
                else:
                    parent_children[name] = [parent_children[name], attr_text_dict]
            else:
                parent_children[name] = attr_text_dict
        else:
            # This is root element
            root = {name: attr_text_dict}

    def char_data(data):
        text_buffer.append(data)

    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    parser.CharacterDataHandler = char_data

    parser.Parse(xml_input, True)

    return root


def unparse(mapping, encoding='utf-8', pretty=False, indent='  ', full_document=True, **kwargs):
    """
    Convert a dictionary back into an XML string.

    Parameters:
    - mapping: dict to convert.
    - encoding: output encoding (default utf-8).
    - pretty: if True, pretty-print with indentation.
    - indent: string to use for indentation.
    - full_document: if True, include XML declaration.
    - kwargs: ignored for compatibility.

    Returns:
    - XML string.
    """
    from xml.sax.saxutils import escape, quoteattr

    def _is_dict(obj):
        return isinstance(obj, dict)

    def _is_list(obj):
        return isinstance(obj, list)

    def _serialize(key, value, level=0):
        # key: element name
        # value: dict or string or list
        # returns string XML fragment

        pad = (indent * level) if pretty else ''

        if value is None:
            # Empty element
            return f"{pad}<{key}/>" + (('\n' if pretty else ''))

        if isinstance(value, str):
            # Text content only
            return f"{pad}<{key}>{escape(value)}</{key}>" + (('\n' if pretty else ''))

        if _is_list(value):
            # Multiple elements with same key
            result = []
            for item in value:
                result.append(_serialize(key, item, level))
            return ''.join(result)

        if _is_dict(value):
            # Separate attributes and children/text
            attrs = []
            children = []
            text = None

            for k, v in value.items():
                if k.startswith('@'):
                    # attribute
                    attr_name = k[1:]
                    attrs.append(f'{attr_name}={quoteattr(str(v))}')
                elif k == '#text':
                    text = v
                else:
                    children.append((k, v))

            attr_str = ''
            if attrs:
                attr_str = ' ' + ' '.join(attrs)

            if not children and (text is None or text == ''):
                # Empty element with attributes only
                return f"{pad}<{key}{attr_str}/>" + (('\n' if pretty else ''))

            # Start tag
            start_tag = f"{pad}<{key}{attr_str}>"
            end_tag = f"</{key}>" + (('\n' if pretty else ''))

            # Children serialization
            if children:
                # If pretty, children on new lines with indentation
                if pretty:
                    child_strs = []
                    for ck, cv in children:
                        child_strs.append(_serialize(ck, cv, level + 1))
                    if text is not None and text.strip() != '':
                        # Text and children mixed: text inline after start tag
                        # This is rare, but we handle by putting text before children
                        text_escaped = escape(text)
                        inner = text_escaped + '\n' + ''.join(child_strs)
                    else:
                        inner = '\n' + ''.join(child_strs) + pad
                else:
                    # No pretty, children inline
                    child_strs = []
                    for ck, cv in children:
                        child_strs.append(_serialize(ck, cv, 0))
                    if text is not None and text.strip() != '':
                        text_escaped = escape(text)
                        inner = text_escaped + ''.join(child_strs)
                    else:
                        inner = ''.join(child_strs)
            else:
                # No children, only text
                inner = escape(text) if text else ''

            return start_tag + inner + end_tag

        # Fallback: convert to string text
        return f"{pad}<{key}>{escape(str(value))}</{key}>" + (('\n' if pretty else ''))

    # mapping should have exactly one root element
    if not _is_dict(mapping) or len(mapping) != 1:
        raise ValueError("Expected a single root element dict")

    root_key = next(iter(mapping))
    root_value = mapping[root_key]

    xml_declaration = ''
    if full_document:
        xml_declaration = f'<?xml version="1.0" encoding="{encoding}"?>' + (('\n' if pretty else ''))

    xml_body = _serialize(root_key, root_value, 0)

    return xml_declaration + xml_body