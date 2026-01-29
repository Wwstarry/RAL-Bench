import humanize


def test_imports_and_exports():
    assert hasattr(humanize, "intcomma")
    assert hasattr(humanize, "ordinal")
    assert hasattr(humanize, "naturalsize")
    assert hasattr(humanize, "precisedelta")
    assert hasattr(humanize, "naturaldelta")
    assert hasattr(humanize, "naturaltime")