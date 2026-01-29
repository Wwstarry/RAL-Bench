"""Tests for mailpile.util module."""

import pytest
from mailpile.util import CleanText, Base36, slugify, truncate, safe_int


class TestCleanText:
    """Test CleanText class."""
    
    def test_clean_whitespace_collapse(self):
        """Test collapsing whitespace."""
        text = "hello   world  \n  test"
        result = CleanText.clean_whitespace(text, collapse=True)
        assert result == "hello world test"
    
    def test_clean_whitespace_no_collapse(self):
        """Test preserving whitespace structure."""
        text = "hello   world"
        result = CleanText.clean_whitespace(text, collapse=False)
        assert result == "hello   world"
    
    def test_remove_control_chars(self):
        """Test removing control characters."""
        text = "hello\x00world\x1ftest"
        result = CleanText.remove_control_chars(text)
        assert result == "helloworldtest"
    
    def test_normalize_unicode(self):
        """Test unicode normalization."""
        text = "café"  # é as single character
        result = CleanText.normalize_unicode(text, form='NFD')
        # NFD decomposes é into e + combining accent
        assert len(result) > len(text)
    
    def test_sanitize_full(self):
        """Test full sanitization."""
        text = "  hello\x00  world  \n  test  "
        result = CleanText.sanitize(text)
        assert result == "hello world test"
    
    def test_sanitize_selective(self):
        """Test selective sanitization."""
        text = "  hello\x00world  "
        result = CleanText.sanitize(text, remove_control=True,
                                    normalize=False, collapse_ws=True)
        assert result == "helloworld"


class TestBase36:
    """Test Base36 encoding/decoding."""
    
    def test_encode_zero(self):
        """Test encoding zero."""
        assert Base36.encode(0) == '0'
    
    def test_encode_positive(self):
        """Test encoding positive integers."""
        assert Base36.encode(35) == 'z'
        assert Base36.encode(36) == '10'
        assert Base36.encode(1296) == '100'
    
    def test_encode_negative(self):
        """Test encoding negative integers."""
        assert Base36.encode(-1) == '-1'
        assert Base36.encode(-36) == '-10'
    
    def test_decode_zero(self):
        """Test decoding zero."""
        assert Base36.decode('0') == 0
    
    def test_decode_positive(self):
        """Test decoding positive values."""
        assert Base36.decode('z') == 35
        assert Base36.decode('10') == 36
        assert Base36.decode('100') == 1296
    
    def test_decode_negative(self):
        """Test decoding negative values."""
        assert Base36.decode('-1') == -1
        assert Base36.decode('-10') == -36
    
    def test_encode_decode_roundtrip(self):
        """Test encode/decode roundtrip."""
        for num in [0, 1, 35, 36, 100, 1000, -1, -100]:
            encoded = Base36.encode(num)
            decoded = Base36.decode(encoded)
            assert decoded == num
    
    def test_decode_invalid(self):
        """Test decoding invalid base36."""
        with pytest.raises(ValueError):
            Base36.decode('xyz!')


class TestSlugify:
    """Test slugify function."""
    
    def test_slugify_basic(self):
        """Test basic slugification."""
        assert slugify('Hello World') == 'hello-world'
    
    def test_slugify_special_chars(self):
        """Test removing special characters."""
        assert slugify('Hello, World!') == 'hello-world'
    
    def test_slugify_unicode(self):
        """Test unicode handling."""
        result = slugify('Café')
        assert 'caf' in result
    
    def test_slugify_multiple_spaces(self):
        """Test handling multiple spaces."""
        assert slugify('Hello   World') == 'hello-world'
    
    def test_slugify_custom_separator(self):
        """Test custom separator."""
        assert slugify('Hello World', separator='_') == 'hello_world'


class TestTruncate:
    """Test truncate function."""
    
    def test_truncate_no_truncation(self):
        """Test when text is shorter than limit."""
        assert truncate('hello', 10) == 'hello'
    
    def test_truncate_with_truncation(self):
        """Test truncating long text."""
        result = truncate('hello world', 8)
        assert result == 'hello...'
        assert len(result) == 8
    
    def test_truncate_custom_suffix(self):
        """Test custom truncation suffix."""
        result = truncate('hello world', 8, suffix='>>>')
        assert result == 'hello>>>'
    
    def test_truncate_exact_length(self):
        """Test text exactly at limit."""
        assert truncate('hello', 5) == 'hello'


class TestSafeInt:
    """Test safe_int function."""
    
    def test_safe_int_from_string(self):
        """Test converting string to int."""
        assert safe_int('42') == 42
    
    def test_safe_int_from_int(self):
        """Test converting int to int."""
        assert safe_int(42) == 42
    
    def test_safe_int_from_float(self):
        """Test converting float to int."""
        assert safe_int(42.7) == 42
    
    def test_safe_int_invalid_string(self):
        """Test invalid string returns default."""
        assert safe_int('not a number') == 0
    
    def test_safe_int_custom_default(self):
        """Test custom default value."""
        assert safe_int('invalid', default=-1) == -1
    
    def test_safe_int_none(self):
        """Test None returns default."""
        assert safe_int(None) == 0