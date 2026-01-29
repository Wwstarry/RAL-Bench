import unittest
import subprocess
import sys
import os
import io

from mailpile import safe_popen, util, vcard, i18n


class TestSafePopen(unittest.TestCase):

    def test_basic_subprocess(self):
        with safe_popen.SafePopen([sys.executable, '-c', 'print("hello")']) as proc:
            out, err = proc.communicate()
            self.assertEqual(out.strip(), b'hello')
            self.assertEqual(err, b'')

    def test_pipe_reader(self):
        output = []

        def callback(line):
            output.append(line)

        with safe_popen.SafePopen([sys.executable, '-c', 'print("line1"); print("line2")'], stdout=subprocess.PIPE) as proc:
            thread = safe_popen.pipe_reader(proc.stdout, callback)
            proc.wait()
            thread.join()

        # Lines include newline bytes
        self.assertIn(b'line1\n', output)
        self.assertIn(b'line2\n', output)


class TestUtil(unittest.TestCase):

    def test_clean_text(self):
        dirty = "Hello\x00\x01 World!\nNew\tLine"
        cleaner = util.CleanText(dirty)
        cleaned = cleaner.clean()
        self.assertEqual(cleaned, "Hello World! New Line")

    def test_base36_encode_decode(self):
        for number in [0, 1, 10, 35, 36, 123456789]:
            encoded = util.base36_encode(number)
            decoded = util.base36_decode(encoded)
            self.assertEqual(number, decoded)

    def test_is_email_address(self):
        self.assertTrue(util.is_email_address("test@example.com"))
        self.assertFalse(util.is_email_address("not-an-email"))
        self.assertFalse(util.is_email_address("test@com"))
        self.assertFalse(util.is_email_address(""))

    def test_safe_str(self):
        class BadStr:
            def __str__(self):
                raise Exception("bad")
        self.assertEqual(util.safe_str("hello"), "hello")
        self.assertTrue(util.safe_str(BadStr()).startswith('<'))


class TestVCard(unittest.TestCase):

    def test_parse_simple(self):
        line = "FN:John Doe"
        vline = vcard.VCardLine.parse(line)
        self.assertEqual(vline.name, "FN")
        self.assertEqual(vline.params, {})
        self.assertEqual(vline.value, "John Doe")

    def test_parse_with_params(self):
        line = "TEL;TYPE=HOME;VALUE=uri:tel:+1-111-555-1212"
        vline = vcard.VCardLine.parse(line)
        self.assertEqual(vline.name, "TEL")
        self.assertEqual(vline.params, {"TYPE": "HOME", "VALUE": "uri"})
        self.assertEqual(vline.value, "tel:+1-111-555-1212")

    def test_serialize(self):
        vline = vcard.VCardLine("EMAIL", {"TYPE": "INTERNET", "PREF": None}, "john@example.com")
        serialized = vline.serialize()
        # Order of params is not guaranteed, so test parts
        self.assertTrue(serialized.startswith("EMAIL"))
        self.assertIn("TYPE=INTERNET", serialized)
        self.assertIn("PREF", serialized)
        self.assertTrue(serialized.endswith("john@example.com"))


class TestI18n(unittest.TestCase):

    def test_gettext(self):
        self.assertEqual(i18n.gettext("hello"), "hello")

    def test_ngettext(self):
        self.assertEqual(i18n.ngettext("one", "many", 1), "one")
        self.assertEqual(i18n.ngettext("one", "many", 2), "many")


if __name__ == '__main__':
    unittest.main()