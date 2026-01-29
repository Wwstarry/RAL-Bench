import unittest
from mailpile.safe_popen import safe_popen, pipe_output
from mailpile.util import CleanText, base36_encode, base36_decode
from mailpile.vcard import VCardLine
from mailpile.i18n import gettext_passthrough

class TestSafePopen(unittest.TestCase):
    def test_safe_popen(self):
        process = safe_popen(['echo', 'hello'], stdout=subprocess.PIPE)
        stdout, _ = pipe_output(process)
        self.assertEqual(stdout.decode().strip(), 'hello')

class TestUtil(unittest.TestCase):
    def test_CleanText(self):
        self.assertEqual(CleanText("  hello  "), "hello")
        self.assertEqual(CleanText("hello!", banned_chars="!"), "hello")

    def test_base36_encode(self):
        self.assertEqual(base36_encode(12345), '9ix')
        self.assertEqual(base36_encode(0), '0')

    def test_base36_decode(self):
        self.assertEqual(base36_decode('9ix'), 12345)
        self.assertEqual(base36_decode('0'), 0)

class TestVCardLine(unittest.TestCase):
    def test_parse(self):
        line = "FN;CHARSET=UTF-8:John Doe"
        vcard = VCardLine.parse(line)
        self.assertEqual(vcard.key, "FN")
        self.assertEqual(vcard.value, "John Doe")
        self.assertEqual(vcard.params, {"CHARSET": "UTF-8"})

    def test_serialize(self):
        vcard = VCardLine("FN", "John Doe", {"CHARSET": "UTF-8"})
        self.assertEqual(vcard.serialize(), "FN;CHARSET=UTF-8:John Doe")

class TestI18n(unittest.TestCase):
    def test_gettext_passthrough(self):
        self.assertEqual(gettext_passthrough("hello"), "hello")

if __name__ == '__main__':
    unittest.main()