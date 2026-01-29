import pytest
import subprocess
import sys

from mailpile.i18n import _
from mailpile.safe_popen import safe_popen
from mailpile.util import b36_encode, b36_decode, CleanText
from mailpile.vcard import VCardLine

# --- i18n Benchmarks ---

def test_benchmark_i18n_passthrough(benchmark):
    """Benchmark the overhead of the i18n passthrough function."""
    benchmark(lambda: _("This is a test string for translation."))

# --- safe_popen Benchmarks ---

def test_benchmark_safe_popen(benchmark):
    """Benchmark launching a trivial process."""
    if sys.platform == 'win32':
        command = ['cmd', '/c', 'echo', 'ok']
    else:
        command = ['true']
    
    def run_command():
        proc = safe_popen(command, stdout=subprocess.PIPE)
        proc.communicate()

    benchmark(run_command)

# --- util Benchmarks ---

def test_benchmark_b36_encode(benchmark):
    """Benchmark base36 encoding."""
    benchmark(b36_encode, 12345678901234567890)

def test_benchmark_b36_decode(benchmark):
    """Benchmark base36 decoding."""
    encoded_str = b36_encode(12345678901234567890)
    benchmark(b36_decode, encoded_str)

def test_benchmark_clean_text(benchmark):
    """Benchmark the CleanText function."""
    dirty_string = "Here is some text\x00with\x08embedded\x1fcontrol characters that need to be cleaned up." * 10
    benchmark(CleanText, dirty_string)

# --- vcard Benchmarks ---

SIMPLE_VCARD_LINE = "FN:John Fitzgerald Doe"
COMPLEX_VCARD_LINE = "EMAIL;TYPE=INTERNET,PREF;X-CUSTOM=some-value:john.doe.is.a.very.long.name@example.com"

def test_benchmark_vcard_parse_simple(benchmark):
    """Benchmark parsing a simple VCard line."""
    benchmark(VCardLine, SIMPLE_VCARD_LINE)

def test_benchmark_vcard_parse_complex(benchmark):
    """Benchmark parsing a complex VCard line."""
    benchmark(VCardLine, COMPLEX_VCARD_LINE)

def test_benchmark_vcard_serialize_complex(benchmark):
    """Benchmark serializing a complex VCard line."""
    vcard_line = VCardLine(COMPLEX_VCARD_LINE)
    benchmark(str, vcard_line)