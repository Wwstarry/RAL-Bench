"""
Basic tests for cmd2 functionality.
"""

import unittest
import sys
from io import StringIO

import cmd2


class TestCmd2Basic(unittest.TestCase):
    """Test basic Cmd2 functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = cmd2.Cmd2()
    
    def test_cmd2_instantiation(self):
        """Test that Cmd2 can be instantiated."""
        self.assertIsInstance(self.app, cmd2.Cmd2)
        self.assertIsInstance(self.app, cmd2.Cmd)
    
    def test_parsing_module(self):
        """Test parsing module."""
        parsed = cmd2.parsing.parse_command_line("hello world")
        self.assertEqual(parsed.command, "hello")
        self.assertEqual(parsed.args, "world")
    
    def test_split_args(self):
        """Test argument splitting."""
        args = cmd2.parsing.split_args('arg1 "arg 2" arg3')
        self.assertEqual(args, ['arg1', 'arg 2', 'arg3'])
    
    def test_utils_safe_str(self):
        """Test safe string conversion."""
        result = cmd2.utils.safe_str(42)
        self.assertEqual(result, "42")
    
    def test_command_registration(self):
        """Test command registration via do_* methods."""
        class TestApp(cmd2.Cmd2):
            def do_test(self, args):
                """Test command"""
                self.poutput("test output")
        
        app = TestApp()
        commands = app.get_all_commands()
        self.assertIn("test", commands)
    
    def test_help_command(self):
        """Test help command."""
        class TestApp(cmd2.Cmd2):
            def do_test(self, args):
                """Test command help"""
                pass
        
        app = TestApp()
        help_text = app.get_command_help("test")
        self.assertIn("Test command help", help_text)


class TestCmd2Parsing(unittest.TestCase):
    """Test Cmd2 parsing functionality."""
    
    def test_parse_empty_line(self):
        """Test parsing empty line."""
        parsed = cmd2.parsing.parse_command_line("")
        self.assertEqual(parsed.command, "")
        self.assertEqual(parsed.args, "")
    
    def test_parse_command_only(self):
        """Test parsing command without arguments."""
        parsed = cmd2.parsing.parse_command_line("hello")
        self.assertEqual(parsed.command, "hello")
        self.assertEqual(parsed.args, "")
    
    def test_parse_command_with_args(self):
        """Test parsing command with arguments."""
        parsed = cmd2.parsing.parse_command_line("hello world foo bar")
        self.assertEqual(parsed.command, "hello")
        self.assertEqual(parsed.args, "world foo bar")
    
    def test_parsed_string_argv(self):
        """Test ParsedString argv attribute."""
        parsed = cmd2.parsing.parse_command_line("cmd arg1 arg2")
        self.assertEqual(parsed.argv, ["arg1", "arg2"])


if __name__ == '__main__':
    unittest.main()