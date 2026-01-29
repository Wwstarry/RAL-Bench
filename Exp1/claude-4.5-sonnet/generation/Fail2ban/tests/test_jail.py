"""
Tests for fail2ban.server.jail module
"""

import unittest
from fail2ban.server.jail import Jail


class TestJail(unittest.TestCase):
    """Test Jail class"""
    
    def test_jail_creation(self):
        """Test jail creation"""
        jail = Jail('sshd')
        self.assertEqual(jail.getName(), 'sshd')
        self.assertFalse(jail.isEnabled())
    
    def test_jail_enable(self):
        """Test enabling jail"""
        jail = Jail('sshd')
        jail.setEnabled(True)
        self.assertTrue(jail.isEnabled())
        
        jail.setEnabled(False)
        self.assertFalse(jail.isEnabled())
    
    def test_jail_max_retry(self):
        """Test max retry setting"""
        jail = Jail('sshd')
        jail.setMaxRetry(10)
        self.assertEqual(jail.getMaxRetry(), 10)
        self.assertEqual(jail.filter.max_retry, 10)
    
    def test_jail_find_time(self):
        """Test find time setting"""
        jail = Jail('sshd')
        jail.setFindTime(300)
        self.assertEqual(jail.getFindTime(), 300)
        self.assertEqual(jail.filter.find_time, 300)
    
    def test_jail_ban_time(self):
        """Test ban time setting"""
        jail = Jail('sshd')
        jail.setBanTime(1200)
        self.assertEqual(jail.getBanTime(), 1200)
    
    def test_jail_log_path(self):
        """Test log path management"""
        jail = Jail('sshd')
        jail.addLogPath('/var/log/auth.log')
        jail.addLogPath('/var/log/secure')
        
        paths = jail.getLogPath()
        self.assertEqual(len(paths), 2)
        self.assertIn('/var/log/auth.log', paths)
        self.assertIn('/var/log/secure', paths)
    
    def test_jail_log_path_duplicate(self):
        """Test adding duplicate log path"""
        jail = Jail('sshd')
        jail.addLogPath('/var/log/auth.log')
        jail.addLogPath('/var/log/auth.log')
        
        paths = jail.getLogPath()
        self.assertEqual(len(paths), 1)
    
    def test_jail_fail_regex(self):
        """Test adding fail regex"""
        jail = Jail('sshd')
        jail.addFailRegex(r'Failed password')
        self.assertEqual(len(jail.filter.failregex), 1)
    
    def test_jail_ignore_regex(self):
        """Test adding ignore regex"""
        jail = Jail('sshd')
        jail.addIgnoreRegex(r'from 127\.0\.0\.1')
        self.assertEqual(len(jail.filter.ignoreregex), 1)
    
    def test_jail_actions(self):
        """Test action management"""
        jail = Jail('sshd')
        jail.addAction('iptables')
        jail.addAction('sendmail')
        
        actions = jail.getActions()
        self.assertEqual(len(actions), 2)
        self.assertIn('iptables', actions)
        self.assertIn('sendmail', actions)
    
    def test_jail_process_line(self):
        """Test processing log line through jail"""
        jail = Jail('sshd')
        jail.addFailRegex(r'Failed password')
        jail.setMaxRetry(2)
        
        # First failure
        result = jail.processLine('Failed password for user from 10.0.0.1')
        self.assertEqual(len(result), 0)
        
        # Second failure
        result = jail.processLine('Failed password for user from 10.0.0.1')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], '10.0.0.1')
    
    def test_jail_get_filter(self):
        """Test getting jail filter"""
        jail = Jail('sshd')
        f = jail.getFilter()
        self.assertIsNotNone(f)
        self.assertEqual(f.jail_name, 'sshd')


if __name__ == '__main__':
    unittest.main()