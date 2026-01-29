"""
Tests for fail2ban.server.filter module
"""

import unittest
from fail2ban.server.filter import isValidIP, searchIP, Filter


class TestIPValidation(unittest.TestCase):
    """Test IP validation functions"""
    
    def test_isValidIP_ipv4(self):
        """Test IPv4 validation"""
        self.assertTrue(isValidIP('192.168.1.1'))
        self.assertTrue(isValidIP('10.0.0.1'))
        self.assertTrue(isValidIP('127.0.0.1'))
        self.assertTrue(isValidIP('255.255.255.255'))
    
    def test_isValidIP_ipv4_invalid(self):
        """Test invalid IPv4 addresses"""
        self.assertFalse(isValidIP('256.1.1.1'))
        self.assertFalse(isValidIP('192.168.1'))
        self.assertFalse(isValidIP('192.168.1.1.1'))
        self.assertFalse(isValidIP('not.an.ip.address'))
    
    def test_isValidIP_ipv6(self):
        """Test IPv6 validation"""
        self.assertTrue(isValidIP('::1'))
        self.assertTrue(isValidIP('2001:0db8:85a3:0000:0000:8a2e:0370:7334'))
    
    def test_isValidIP_empty(self):
        """Test empty input"""
        self.assertFalse(isValidIP(''))
        self.assertFalse(isValidIP(None))
    
    def test_searchIP_single(self):
        """Test searching for single IP"""
        ips = searchIP('Connection from 192.168.1.100')
        self.assertEqual(len(ips), 1)
        self.assertEqual(ips[0], '192.168.1.100')
    
    def test_searchIP_multiple(self):
        """Test searching for multiple IPs"""
        ips = searchIP('From 10.0.0.1 to 192.168.1.1')
        self.assertEqual(len(ips), 2)
        self.assertIn('10.0.0.1', ips)
        self.assertIn('192.168.1.1', ips)
    
    def test_searchIP_none(self):
        """Test searching with no IPs"""
        ips = searchIP('No IP addresses here')
        self.assertEqual(len(ips), 0)
    
    def test_searchIP_empty(self):
        """Test searching empty string"""
        ips = searchIP('')
        self.assertEqual(len(ips), 0)


class TestFilter(unittest.TestCase):
    """Test Filter class"""
    
    def test_filter_creation(self):
        """Test filter creation"""
        f = Filter('test-jail')
        self.assertEqual(f.jail_name, 'test-jail')
        self.assertEqual(f.max_retry, 5)
        self.assertEqual(f.find_time, 600)
    
    def test_add_fail_regex(self):
        """Test adding fail regex"""
        f = Filter('test-jail')
        f.addFailRegex(r'Failed password for .* from <HOST>')
        self.assertEqual(len(f.failregex), 1)
    
    def test_add_ignore_regex(self):
        """Test adding ignore regex"""
        f = Filter('test-jail')
        f.addIgnoreRegex(r'from 127\.0\.0\.1')
        self.assertEqual(len(f.ignoreregex), 1)
    
    def test_process_line_match(self):
        """Test processing matching line"""
        f = Filter('test-jail')
        f.addFailRegex(r'Failed password')
        f.max_retry = 2
        
        # First failure
        result = f.processLine('Failed password for user from 192.168.1.100')
        self.assertEqual(len(result), 0)  # Not banned yet
        
        # Second failure - should trigger ban
        result = f.processLine('Failed password for user from 192.168.1.100')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], '192.168.1.100')
    
    def test_process_line_ignore(self):
        """Test processing ignored line"""
        f = Filter('test-jail')
        f.addFailRegex(r'Failed password')
        f.addIgnoreRegex(r'from 127\.0\.0\.1')
        
        result = f.processLine('Failed password for user from 127.0.0.1')
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()