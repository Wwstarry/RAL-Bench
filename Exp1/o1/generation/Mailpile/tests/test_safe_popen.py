import unittest
import os
from mailpile.safe_popen import run_command

class TestSafePopen(unittest.TestCase):
    def test_run_command_echo(self):
        rc, out, err = run_command(['echo', 'Hello'])
        self.assertEqual(rc, 0)
        self.assertIn('Hello', out.strip())
        self.assertEqual(err, '')

    def test_run_command_with_input(self):
        rc, out, err = run_command(['cat'], input_data='Hello World')
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), 'Hello World')
        self.assertEqual(err, '')

    def test_run_command_invalid(self):
        rc, out, err = run_command(['non-existent-command'])
        self.assertNotEqual(rc, 0)
        self.assertEqual(out, '')
        self.assertTrue(err)