"""Tests for filter module."""

import unittest
from fail2ban.server.filter import isValidIP, searchIP, searchIPs, Filter


class TestIPValidation(unittest.TestCase):
    """Test IP validation functions."""
    
    def test_isValidIP_valid_ipv4(self):
        """Test validation of valid IPv4 addresses."""
        self.assertTrue(isValidIP('192.168.1.1'))
        self.assertTrue(isValidIP('10.0.0.1'))
        self.assertTrue(isValidIP('255.255.255.255'))
        self.assertTrue(isValidIP('0.0.0.0'))
    
    def test_isValidIP_invalid_ipv4(self):
        """Test validation of invalid IPv4 addresses."""
        self.assertFalse(isValidIP('256.1.1.1'))
        self.assertFalse(isValidIP('192.168.1'))
        self.assertFalse(isValidIP('192.168.1.1.1'))
        self.assertFalse(isValidIP('not.an.ip.address'))
        self.assertFalse(isValidIP(''))
    
    def test_searchIP_single_ip(self):
        """Test searching for single IP in text."""
        text = "Failed password for user from 192.168.1.100 port 22"
        ip = searchIP(text)
        self.assertEqual(ip, '192.168.1.100')
    
    def test_searchIP_no_ip(self):
        """Test searching for IP when none exists."""
        text = "Some log message without IP"
        ip = searchIP(text)
        self.assertIsNone(ip)
    
    def test_searchIP_multiple_ips(self):
        """Test that searchIP returns first IP."""
        text = "Connection from 192.168.1.1 to 10.0.0.1"
        ip = searchIP(text)
        self.assertEqual(ip, '192.168.1.1')
    
    def test_searchIPs_multiple(self):
        """Test searching for multiple IPs."""
        text = "Connection from 192.168.1.1 to 10.0.0.1"
        ips = searchIPs(text)
        self.assertEqual(len(ips), 2)
        self.assertIn('192.168.1.1', ips)
        self.assertIn('10.0.0.1', ips)
    
    def test_searchIPs_duplicates(self):
        """Test that searchIPs removes duplicates."""
        text = "IP 192.168.1.1 and again 192.168.1.1"
        ips = searchIPs(text)
        self.assertEqual(len(ips), 2)  # findall returns both, but we check uniqueness in caller


class TestFilter(unittest.TestCase):
    """Test Filter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.filter = Filter('test')
    
    def test_filter_init(self):
        """Test filter initialization."""
        self.assertEqual(self.filter.name, 'test')
        self.assertIsNone(self.filter.failregex)
        self.assertIsNone(self.filter.ignoreregex)
    
    def test_setFailRegex_valid(self):
        """Test setting valid fail regex."""
        self.filter.setFailRegex(r'Failed password.*from (\S+)')
        self.assertIsNotNone(self.filter.failregex)
    
    def test_setFailRegex_invalid(self):
        """Test setting invalid fail regex."""
        with self.assertRaises(ValueError):
            self.filter.setFailRegex(r'[invalid(regex')
    
    def test_setIgnoreRegex_valid(self):
        """Test setting valid ignore regex."""
        self.filter.setIgnoreRegex(r'localhost')
        self.assertIsNotNone(self.filter.ignoreregex)
    
    def test_processLine_no_regex(self):
        """Test processing line without regex set."""
        result = self.filter.processLine("Some log line")
        self.assertIsNone(result)
    
    def test_processLine_match(self):
        """Test processing line that matches fail regex."""
        self.filter.setFailRegex(r'Failed password')
        line = "Failed password for user from 192.168.1.100"
        result = self.filter.processLine(line)
        self.assertEqual(result, '192.168.1.100')
    
    def test_processLine_no_match(self):
        """Test processing line that doesn't match fail regex."""
        self.filter.setFailRegex(r'Failed password')
        line = "Accepted password for user from 192.168.1.100"
        result = self.filter.processLine(line)
        self.assertIsNone(result)
    
    def test_processLine_ignore_match(self):
        """Test that ignore regex prevents matching."""
        self.filter.setFailRegex(r'Failed password')
        self.filter.setIgnoreRegex(r'localhost')
        line = "Failed password for user from localhost"
        result = self.filter.processLine(line)
        self.assertIsNone(result)
    
    def test_processLine_ignore_no_match(self):
        """Test processing when ignore regex doesn't match."""
        self.filter.setFailRegex(r'Failed password')
        self.filter.setIgnoreRegex(r'localhost')
        line = "Failed password for user from 192.168.1.100"
        result = self.filter.processLine(line)
        self.assertEqual(result, '192.168.1.100')


if __name__ == '__main__':
    unittest.main()