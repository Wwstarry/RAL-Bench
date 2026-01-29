import unittest
import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fail2ban.server.jail import Jail
from fail2ban.server.filter import isValidIP, searchIP

class TestFail2BanCore(unittest.TestCase):
    def test_jail_initialization(self):
        j = Jail("test_jail")
        self.assertEqual(j.name, "test_jail")
        self.assertFalse(j.is_alive())
        j.start()
        self.assertTrue(j.is_alive())
        j.stop()
        self.assertFalse(j.is_alive())

    def test_filter_helpers(self):
        # Test isValidIP
        self.assertTrue(isValidIP("192.168.1.1"))
        self.assertFalse(isValidIP("999.999.999.999"))
        self.assertFalse(isValidIP("abc"))

        # Test searchIP
        line = "Failed password for root from 10.0.0.5 port 22 ssh2"
        match = searchIP(line)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(0), "10.0.0.5")

        line_no_ip = "Failed password for root from nowhere"
        match = searchIP(line_no_ip)
        self.assertIsNone(match)

if __name__ == "__main__":
    unittest.main()