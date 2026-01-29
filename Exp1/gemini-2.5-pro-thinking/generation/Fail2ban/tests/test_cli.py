# tests/test_cli.py
import unittest
import subprocess
import os
import sys

class TestCLI(unittest.TestCase):

    def setUp(self):
        self.log_file = "test_cli_auth.log"
        with open(self.log_file, "w") as f:
            f.write("Sep 10 10:10:01 server sshd[1]: Failed password for user from 1.2.3.4\n")
            f.write("Sep 10 10:10:02 server sshd[2]: Accepted password for user from 5.6.7.8\n")
            f.write("Sep 10 10:10:03 server sshd[3]: Failed password for invalid user admin from 1.2.3.4\n")
        
        self.config_file = "test_jail.conf"
        with open(self.config_file, "w") as f:
            f.write("[sshd]\n")
            f.write("failregex = Failed password for .* from <HOST>\n")

    def tearDown(self):
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def _run_script(self, script_path, args):
        # We need to ensure the 'fail2ban' package is in the python path
        # when running the script via subprocess.
        env = os.environ.copy()
        env['PYTHONPATH'] = '.' + os.pathsep + env.get('PYTHONPATH', '')
        cmd = [sys.executable, script_path] + args
        return subprocess.run(cmd, capture_output=True, text=True, check=True, env=env)

    def test_server_help(self):
        result = self._run_script('bin/fail2ban-server', ['--help'])
        self.assertIn("usage: fail2ban-server", result.stdout)
        self.assertIn("Fail2Ban server daemon", result.stdout)

    def test_client_help(self):
        result = self._run_script('bin/fail2ban-client', ['--help'])
        self.assertIn("usage: fail2ban-client", result.stdout)
        self.assertIn("Fail2Ban client utility", result.stdout)

    def test_regex_cli_with_string(self):
        regex = "Failed password for .* from <HOST>"
        result = self._run_script('bin/fail2ban-regex', [self.log_file, regex])
        
        self.assertIn("Results", result.stdout)
        self.assertIn("Lines: 3 lines", result.stdout)
        self.assertIn("Matched: 2 lines", result.stdout)
        self.assertIn("Missed: 1 lines", result.stdout)
        self.assertIn("MATCH: 'Sep 10 10:10:01 server sshd[1]: Failed password for user from 1.2.3.4'", result.stdout)

    def test_regex_cli_with_config(self):
        result = self._run_script('bin/fail2ban-regex', [self.log_file, self.config_file])
        
        self.assertIn("Results", result.stdout)
        self.assertIn("Lines: 3 lines", result.stdout)
        self.assertIn("Matched: 2 lines", result.stdout)
        self.assertIn("Missed: 1 lines", result.stdout)

if __name__ == '__main__':
    unittest.main()