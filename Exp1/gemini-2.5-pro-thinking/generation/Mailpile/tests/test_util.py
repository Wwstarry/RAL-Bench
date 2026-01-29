from mailpile.util import b36_encode, b36_decode, CleanText, friendly_time

def test_b36_roundtrip():
    """Test that encoding and decoding a number returns the original."""
    test_numbers = [0, 1, 35, 36, 123456789, 9876543210]
    for num in test_numbers:
        encoded = b36_encode(num)
        decoded = b36_decode(encoded)
        assert decoded == num

def test_b36_known_values():
    """Test base36 encoding against known values."""
    assert b36_encode(10) == 'a'
    assert b36_encode(35) == 'z'
    assert b36_encode(36) == '10'
    assert b36_encode(0) == '0'

def test_clean_text():
    """Test the CleanText utility function."""
    # String with control characters
    bad_string = "hello\x00world\x1fthis is a test\x7f"
    cleaned = CleanText(bad_string)
    assert cleaned == "hello?world?this is a test?"

    # String with allowed whitespace
    good_string = "line 1\nline 2\t- indented\r\n"
    assert CleanText(good_string) == good_string

    # Empty string
    assert CleanText("") == ""

def test_friendly_time():
    """Test the friendly_time utility."""
    assert friendly_time(5.5) == "5.5s"
    assert friendly_time(90) == "1.5m"
    assert friendly_time(3600) == "1.0h"
    assert friendly_time(5400) == "1.5h"