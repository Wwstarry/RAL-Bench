import xmltodict


def test_escaping_text_and_attrs_roundtrip():
    m = {"a": {"@x": '1&2"3\'4<5>', "#text": "a&b<c>d"}}
    xml = xmltodict.unparse(m, full_document=False)
    # Ensure parse returns same mapping
    assert xmltodict.parse(xml) == m


def test_short_empty_elements_toggle():
    m = {"a": {"b": None}}
    xml_short = xmltodict.unparse(m, full_document=False, short_empty_elements=True)
    assert "<b/>" in xml_short

    xml_long = xmltodict.unparse(m, full_document=False, short_empty_elements=False)
    assert "<b></b>" in xml_long

    assert xmltodict.parse(xml_short) == m
    assert xmltodict.parse(xml_long) == m