import unittest
from mailpile.vcard import parse_vcard_line, VCardLine

class TestVCard(unittest.TestCase):

    def test_parse_simple_line(self):
        line = "FN:John Doe"
        vcl = parse_vcard_line(line)
        self.assertEqual(vcl.key, "FN")
        self.assertEqual(vcl.value, "John Doe")
        self.assertEqual(vcl.params, {})

    def test_parse_line_with_params(self):
        line = "TEL;TYPE=home:1234567"
        vcl = parse_vcard_line(line)
        self.assertEqual(vcl.key, "TEL")
        self.assertEqual(vcl.value, "1234567")
        self.assertIn('type', vcl.params)
        self.assertEqual(vcl.params['type'], 'home')

    def test_serialize(self):
        vcl = VCardLine("EMAIL", "john@example.com", params={"type": "work"})
        serialized = vcl.serialize()
        self.assertEqual(serialized, "EMAIL;TYPE=work:john@example.com")