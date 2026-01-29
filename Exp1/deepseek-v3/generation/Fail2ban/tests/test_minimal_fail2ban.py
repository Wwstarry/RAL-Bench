"""
Tests for minimal Fail2Ban implementation.
All tests are safe and offline.
"""
import unittest
import tempfile
import os
from fail2ban.server.jail import Jail
from fail2ban.server.filter import Filter, isValidIP, searchIP

class TestFilterUtilities(unittest.TestCase):
    """Test IP validation and search functions."""
    
    def test_isValidIP(self):
        """Test IP address validation."""
        self.assertTrue(isValidIP("192.168.1.1"))
        self.assertTrue(isValidIP("::1"))
        self.assertTrue(isValidIP("2001:db8::1"))
        self.assertFalse(isValidIP("not.an.ip"))
        self.assertFalse(isValidIP("256.256.256.256"))
        
    def test_searchIP(self):
        """Test IP address search in text."""
        self.assertEqual(searchIP("Failed login from 192.168.1.1"), "192.168.1.1")
        self.assertEqual(searchIP("Connection from ::1 refused"), "::1")
        self.assertIsNone(searchIP("No IP in this text"))
        self.assertIsNone(searchIP("Invalid IP 999.999.999.999"))

class TestFilter(unittest.TestCase):
    """Test Filter class functionality."""
    
    def test_filter_match(self):
        """Test filter pattern matching."""
        filter_obj = Filter("ssh", r"Failed password for .* from <HOST>")
        line = "Failed password for root from 192.168.1.1 port 22"
        
        match = filter_obj.match(line)
        self.assertIn('matched', match)
        self.assertEqual(match['ip'], "192.168.1.1")
        
    def test_filter_no_match(self):
        """Test filter with non-matching line."""
        filter_obj = Filter("ssh", r"Failed password for .* from <HOST>")
        line = "Successful login from 192.168.1.1"
        
        match = filter_obj.match(line)
        self.assertEqual(match, {})

class TestJail(unittest.TestCase):
    """Test Jail class functionality."""
    
    def setUp(self):
        """Set up test jail."""
        self.jail = Jail("test-jail")
        self.filter = Filter("ssh", r"Failed password for .* from <HOST>")
        self.jail.addFilter(self.filter)
        
    def test_jail_creation(self):
        """Test jail initialization."""
        self.assertEqual(self.jail.name, "test-jail")
        self.assertTrue(self.jail.enabled)
        self.assertEqual(len(self.jail.filters), 1)
        
    def test_jail_process_line(self):
        """Test processing log lines."""
        line = "Failed password for root from 192.168.1.1 port 22"
        result = self.jail.processLine(line, 1234567890.0)
        
        self.assertIn('ip', result)
        self.assertEqual(result['ip'], "192.168.1.1")
        
    def test_jail_ban_unban(self):
        """Test IP banning and unbanning simulation."""
        self.assertTrue(self.jail.banIP("192.168.1.1"))
        self.assertIn("192.168.1.1", self.jail.banned_ips)
        
        self.assertTrue(self.jail.unbanIP("192.168.1.1"))
        self.assertNotIn("192.168.1.1", self.jail.banned_ips)
        
    def test_jail_invalid_ip(self):
        """Test handling of invalid IP addresses."""
        self.assertFalse(self.jail.banIP("invalid.ip"))
        self.assertFalse(self.jail.unbanIP("invalid.ip"))

class TestCLITools(unittest.TestCase):
    """Test command-line tools."""
    
    def test_regex_tool_pattern(self):
        """Test regex tool with basic pattern."""
        # This would test the CLI tool functionality
        # In a real implementation, we'd use subprocess to test the scripts
        pass

if __name__ == '__main__':
    unittest.main()