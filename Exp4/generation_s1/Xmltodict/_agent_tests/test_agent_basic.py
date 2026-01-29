import io
import xmltodict


def test_parse_empty_and_text():
    assert xmltodict.parse("<a/>") == {"a": None}
    assert xmltodict.parse("<a>1</a>") == {"a": "1"}


def test_parse_nested_and_repeated():
    xml = "<a><b>1</b><b>2</b><c><d>3</d></c></a>"
    assert xmltodict.parse(xml) == {"a": {"b": ["1", "2"], "c": {"d": "3"}}}


def test_parse_attributes_and_text():
    xml = "<a x='1'>t</a>"
    assert xmltodict.parse(xml) == {"a": {"@x": "1", "#text": "t"}}

    xml2 = "<a x='1'/>"
    assert xmltodict.parse(xml2) == {"a": {"@x": "1"}}


def test_pretty_printed_whitespace_ignored_between_children():
    xml = "<a>\n  <b>1</b>\n  <c>2</c>\n</a>"
    assert xmltodict.parse(xml) == {"a": {"b": "1", "c": "2"}}


def test_namespace_prefix_preserved_in_names_and_attrs():
    xml = "<ns:root xmlns:ns='u'><ns:child ns:attr='v'>t</ns:child></ns:root>"
    assert xmltodict.parse(xml) == {"ns:root": {"ns:child": {"@ns:attr": "v", "#text": "t"}}}


def test_unparse_roundtrip_basic_cases():
    mappings = [
        {"a": None},
        {"a": "1"},
        {"a": {"@x": "1"}},
        {"a": {"@x": "1", "#text": "t"}},
        {"a": {"b": ["1", "2"], "c": {"@id": "3", "#text": "z"}}},
        {"ns:root": {"ns:child": {"@ns:attr": "v", "#text": "t"}}},
        {"catalog": {"book": [{"@id": "bk101", "author": "A"}, {"@id": "bk102", "author": "B"}]}},
    ]
    for m in mappings:
        xml = xmltodict.unparse(m, full_document=False)
        m2 = xmltodict.parse(xml)
        assert m2 == m


def test_unparse_output_filelike():
    m = {"a": {"b": "1"}}
    f = io.StringIO()
    ret = xmltodict.unparse(m, output=f, full_document=False)
    assert ret is None
    assert xmltodict.parse(f.getvalue()) == m