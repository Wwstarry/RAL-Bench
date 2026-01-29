import pytest

from slugify import slugify as slugify_top
from slugify.slugify import slugify as slugify_mod


def test_imports_work():
    assert slugify_top("a b") == "a-b"
    assert slugify_mod("a b") == "a-b"


def test_basic_ascii_punctuation_whitespace():
    assert slugify_top("Hello, world!") == "hello-world"
    assert slugify_top("  multiple   spaces ") == "multiple-spaces"
    assert slugify_top("a---b___c") == "a-b-c"
    assert slugify_top("...") == ""


def test_lowercase_toggle():
    assert slugify_top("Hello World", lowercase=True) == "hello-world"
    assert slugify_top("Hello World", lowercase=False) == "Hello-World"


def test_allow_unicode_behavior():
    assert slugify_top("Café") == "cafe"
    assert slugify_top("你好 世界", allow_unicode=True) == "你好-世界"
    assert slugify_top("你好 世界", allow_unicode=False) == ""


def test_separator_customization():
    assert slugify_top("Hello world", separator="_") == "hello_world"
    assert slugify_top("Hello world", separator="--") == "hello--world"
    # whitespace separator coerces to '-'
    assert slugify_top("Hello world", separator=" ") == "hello-world"


def test_regex_pattern_prefiltering():
    # Remove digits before slugging
    assert slugify_top("a1 b2 c3", regex_pattern=r"\d+") == "a-b-c"
    # Remove asterisks specifically
    assert slugify_top("a*b*c", regex_pattern=r"\*") == "abc"


def test_stopwords():
    assert slugify_top("the quick and the dead", stopwords=["and", "the"]) == "quick-dead"
    assert slugify_top("The quick", stopwords=["the"]) == "quick"


def test_max_length_no_word_boundary():
    assert slugify_top("hello world", max_length=5, word_boundary=False) == "hello"
    # cut in the middle is allowed
    assert slugify_top("hello world", max_length=7, word_boundary=False) == "hello-w"


def test_max_length_word_boundary():
    assert slugify_top("hello world", max_length=7, word_boundary=True) == "hello"
    # first token longer than max_length => strict word boundary => empty
    assert slugify_top("abcdefghij", max_length=5, word_boundary=True) == ""


def test_replacements():
    assert slugify_top("Tom & Jerry", replacements=[("&", "and")]) == "tom-and-jerry"