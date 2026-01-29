import sys
import pytest

from mailpile.i18n import gettext, _, set_language, get_language
from mailpile.util import CleanText, b36, unb36, safe_str, safe_bytes, truthy
from mailpile.vcard import VCardLine
from mailpile.safe_popen import backtick, SafePopen


def test_i18n_passthrough_and_alias():
    assert gettext("Hello") == "Hello"
    assert _("Hello") == "Hello"
    assert gettext("Héllö") == "Héllö"
    assert gettext(123) == "123"
    set_language(None)
    assert get_language() is None


def test_util_cleantext_basic():
    assert CleanText(None) == ""
    assert CleanText(b"abc") == "abc"
    assert CleanText("a\x00b") == "a b"
    assert CleanText("a@b#c", banned="@#") == "a b c"


def test_util_base36_known_values_and_roundtrip():
    assert b36(0) == "0"
    assert b36(35) == "z"
    assert b36(36) == "10"
    assert unb36("10") == 36
    assert unb36("Z") == 35
    for n in [0, 1, 2, 35, 36, 37, 12345, 10**6]:
        assert unb36(b36(n)) == n
    assert unb36("-10") == -36
    assert b36(-36) == "-10"
    with pytest.raises(ValueError):
        unb36("!")
    with pytest.raises(ValueError):
        unb36("")


def test_util_safe_str_bytes():
    assert safe_str(b"\xff") == "\ufffd"
    assert safe_bytes("x") == b"x"
    assert safe_bytes(None) == b""


def test_util_truthy():
    assert truthy(True) is True
    assert truthy(False) is False
    assert truthy("yes") is True
    assert truthy("no") is False
    assert truthy("0") is False
    assert truthy("1") is True
    assert truthy("maybe") is True  # non-empty fallback


def test_vcard_parse_simple():
    v = VCardLine.Parse("FN:John Doe")
    assert v.name == "FN"
    assert v.group is None
    assert v.params == {}
    assert v.value == "John Doe"
    assert v.as_vcardline() == "FN:John Doe"


def test_vcard_parse_params_and_group():
    v = VCardLine.Parse("item1.EMAIL;TYPE=INTERNET,HOME:me@example.com")
    assert v.group == "item1"
    assert v.name == "EMAIL"
    assert v.params["TYPE"] == ["INTERNET", "HOME"]
    assert v.value == "me@example.com"
    # Deterministic: keys upper, params sorted (only TYPE anyway)
    assert v.as_vcardline() == "item1.EMAIL;TYPE=INTERNET,HOME:me@example.com"


def test_vcard_escaping_roundtrip():
    orig = "a,b;c\\d\n"
    v = VCardLine(name="NOTE", value=orig)
    line = v.as_vcardline()
    assert line == r"NOTE:a\,b\;c\\d\n"
    v2 = VCardLine.Parse(line)
    assert v2.value == orig


def test_safe_popen_backtick_stdout_stderr():
    rc, out, err = backtick([sys.executable, "-c", 'print("hi")'])
    assert rc == 0
    assert out == "hi\n"
    assert err == ""

    rc, out, err = backtick([sys.executable, "-c", 'import sys; sys.stderr.write("err")'])
    assert rc == 0
    assert out == ""
    assert err == "err"


def test_safepopen_disallows_shell_true():
    with pytest.raises(ValueError):
        SafePopen("echo hi", shell=True)

    # List args should work
    p = SafePopen([sys.executable, "-c", "print('ok')"], stdout=sys.stdout.__class__.fileno if False else None)
    # We won't wait here; just ensure object created and is a Popen
    assert hasattr(p, "pid")
    p.terminate()