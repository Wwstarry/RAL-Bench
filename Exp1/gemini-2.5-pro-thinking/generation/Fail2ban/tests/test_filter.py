# tests/test_filter.py
import unittest
from fail2ban.server.filter import isValidIP, searchIP, Filter

class TestFilter(unittest.TestCase):

    def test_isValidIP(self):
        self.assertTrue(isValidIP("192.168.1.1"))
        self.assertTrue(isValidIP("10.0.0.1"))
        self.assertTrue(isValidIP("255.255.255.255"))
        self.assertFalse(isValidIP("256.0.0.1"))
        self.assertFalse(isValidIP("192.168.1"))
        self.assertFalse(isValidIP("not.an.ip"))
        # IPv6
        self.assertTrue(isValidIP("::1"))
        self.assertTrue(isValidIP("2001:0db8:85a3:0000:0000:8a2e:0370:7334"))

    def test_searchIP(self):
        line1 = "Some log line with an IP 192.168.1.1 here."
        self.assertEqual(searchIP(line1), "192.168.1.1")

        line2 = "No IP in this line."
        self.assertIsNone(searchIP(line2))

        line3 = "Invalid IP 999.999.999.999 should not be found."
        self.assertIsNone(searchIP(line3))

        line4 = "First IP 10.0.0.1 should be found, not 10.0.0.2"
        self.assertEqual(searchIP(line4), "10.0.0.1")

    def test_filter_class(self):
        failregex = r"Failed password for .* from <HOST>"
        log_line = "Sep 10 10:10:10 server sshd[1234]: Failed password for user from 1.2.3.4 port 12345 ssh2"
        
        f = Filter(failregex)
        
        self.assertEqual(f.getFailures(log_line), "1.2.3.4")

        no_match_line = "Sep 10 10:10:10 server sshd[1234]: Accepted password for user from 1.2.3.4"
        self.assertIsNone(f.getFailures(no_match_line))

if __name__ == '__main__':
    unittest.main()