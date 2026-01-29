# tests/test_jail.py
import unittest
import time
import os
from fail2ban.server.jail import Jail

class TestJail(unittest.TestCase):

    def setUp(self):
        self.log_file = "test_auth.log"
        with open(self.log_file, "w") as f:
            f.write("Sep 10 10:10:01 server sshd[1]: Failed password for user from 1.2.3.4\n")
            f.write("Sep 10 10:10:02 server sshd[2]: Failed password for user from 1.2.3.4\n")
            f.write("Sep 10 10:10:03 server sshd[3]: Failed password for user from 1.2.3.4\n")
            f.write("Sep 10 10:10:04 server sshd[4]: Failed password for user from 10.0.0.1\n")
            f.write("Sep 10 10:10:05 server sshd[5]: Failed password for user from 1.2.3.4\n")

    def tearDown(self):
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def test_jail_banning_logic(self):
        # Test with a low maxretry to trigger a ban
        jail = Jail(
            name="sshd-test",
            logpath=self.log_file,
            failregex=r"Failed password for .* from <HOST>",
            maxretry=3,
            findtime=60
        )

        self.assertFalse(jail.is_banned("1.2.3.4"))
        self.assertFalse(jail.is_banned("10.0.0.1"))

        # Process the log file
        with open(self.log_file, "r") as f:
            for line in f:
                jail.process_line(line)
        
        # After 3 failures, 1.2.3.4 should be banned
        self.assertTrue(jail.is_banned("1.2.3.4"))
        # 10.0.0.1 only had one failure, should not be banned
        self.assertFalse(jail.is_banned("10.0.0.1"))

    def test_findtime_expiry(self):
        jail = Jail(
            name="sshd-findtime",
            logpath=self.log_file,
            failregex=r"Failed password for .*",
            maxretry=3,
            findtime=2 # very short findtime
        )

        jail.process_line("Failed password for user from 5.6.7.8")
        jail.process_line("Failed password for user from 5.6.7.8")
        
        self.assertEqual(len(jail.failures["5.6.7.8"]), 2)
        self.assertFalse(jail.is_banned("5.6.7.8"))

        # Wait for findtime to expire
        time.sleep(2.1)

        # This failure should be the only one in the new time window
        jail.process_line("Failed password for user from 5.6.7.8")
        self.assertEqual(len(jail.failures["5.6.7.8"]), 1)
        self.assertFalse(jail.is_banned("5.6.7.8"))

if __name__ == '__main__':
    unittest.main()