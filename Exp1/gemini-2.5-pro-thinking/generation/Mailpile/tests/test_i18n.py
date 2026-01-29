from mailpile.i18n import _, set_language

def test_gettext_passthrough():
    """Test that the _() function returns the input string."""
    test_string = "Hello, World!"
    assert _(test_string) == test_string

def test_set_language_is_noop():
    """Test that changing language has no effect in this simplified version."""
    set_language('fr')
    test_string = "This should not be translated."
    assert _(test_string) == test_string
    set_language('en') # Reset for other tests