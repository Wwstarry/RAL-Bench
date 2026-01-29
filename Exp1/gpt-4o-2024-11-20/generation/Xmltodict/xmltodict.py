import re
from xml.sax.saxutils import escape, unescape

def parse(xml_string, process_namespaces=False, strip_whitespace=True):
    """
    Parses an XML string into a nested Python dictionary.

    Args:
        xml_string (str): The XML string to parse.
        process_namespaces (bool): Whether to preserve namespace prefixes in element names.
        strip_whitespace (bool): Whether to strip leading/trailing whitespace from text content.

    Returns:
        dict: A nested dictionary representation of the XML structure.
    """
    def _parse_element(element, parent=None):
        tag = element.group('tag')
        attributes = element.group('attributes')
        content = element.group('content')

        # Process attributes
        attr_dict = {}
        if attributes:
            attr_matches = re.findall(r'(\S+?)="(.*?)"', attributes)
            for attr_name, attr_value in attr_matches:
                attr_dict[f"@{attr_name}"] = unescape(attr_value)

        # Process content
        if content:
            child_elements = re.findall(r'<(?P<tag>[^/][^ >]+)(?P<attributes>[^>]*)>(?P<content>.*?)</\1>', content, re.DOTALL)
            if child_elements:
                children = {}
                for child in child_elements: