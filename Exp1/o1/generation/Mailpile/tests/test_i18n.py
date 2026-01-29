import unittest
from mailpile.i18n import _, gettext_passthrough

class TestI18n(unittest.TestCase):

    def test_gettext_passthrough(self):
        self.assertEqual(gettext_passthrough("Hello"), "Hello")
        self.assertEqual(_("World"), "World")