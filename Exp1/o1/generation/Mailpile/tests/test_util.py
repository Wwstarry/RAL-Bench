import unittest
from mailpile.util import CleanText, int_to_base36, base36_to_int, friendly_number

class TestUtil(unittest.TestCase):

    def test_CleanText(self):
        self.assertEqual(CleanText("Hello!"), "Hello!")
        self.assertEqual(CleanText("Clean?This", banned_chars="?"), "CleanThis")

    def test_base36_conversion(self):
        for original in [0, 1, 10, 35, 36, 123456]:
            b36 = int_to_base36(original)
            back = base36_to_int(b36)
            self.assertEqual(original, back)

    def test_friendly_number(self):
        self.assertEqual(friendly_number(0), "0")
        self.assertEqual(friendly_number(1234), "1,234")
        self.assertEqual(friendly_number(1234567), "1,234,567")