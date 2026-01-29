import cmd
import sys
import os
import argparse
import re
import functools
import traceback
from .parsing import Statement
from .utils import StdSim

# Decorator for argparse integration
def with_argparser(parser, preserve_quotes=False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(cmd_inst, statement):
            # If statement is just a string (legacy cmd), convert to Statement
            if not isinstance(statement, Statement):
                statement = Statement(statement)
            
            # argv[0] is the command, argv[1:] are arguments
            args_list = statement.argv[1:]
            
            try:
                # Parse arguments
                # We suppress exit so argparse doesn't kill the shell on error/-h
                ns = parser.parse_args(args_list)
            except SystemExit:
                # argparse prints help/error to stderr/stdout then calls exit
                # We catch this to keep the shell alive
                return
            except Exception as e:
                cmd_inst.perror(f"Error parsing arguments: {e}")
                return

            return func(cmd_inst, ns)
        
        # Store the parser on the function for help generation
        wrapper.argparser = parser
        return wrapper
    return decorator


class Cmd(cmd.Cmd):
    """
    A drop-in replacement for cmd.Cmd with enhanced features.
    """
    
    def __init__(self, completekey='tab', stdin=None, stdout=None):
        super().__init__(completekey, stdin, stdout)
        if self.stdout is None:
            self.stdout = sys.stdout
        
        # Support for transcript testing
        self._in_transcript = False
        self.exit_code = 0

    def poutput(self, msg='', end='\n'):
        """
        Print message to self.stdout.
        """
        if msg is not None:
            print(msg, end=end, file=self.stdout)

    def perror(self, msg='', end='\n'):
        """
        Print error message to sys.stderr (or self.stdout if redirected).
        """
        if msg is not None:
            # In standard cmd2, perror often goes to stderr, but respects redirection context
            print(msg, end=end, file=sys.stderr)

    def pfeedback(self, msg='', end='\n'):
        """
        Print feedback (informational) message.
        """
        self.poutput(msg, end=end)

    def onecmd(self, line):
        """
        Interpret the argument as though it had been typed in response
        to the prompt.
        """
        statement = Statement(line)
        
        # Handle Redirection
        saved_stdout = self.stdout
        try:
            if statement.output:
                mode = 'a' if statement.output == '>>' else 'w'
                try:
                    self.stdout = open(statement.output_to, mode)
                except IOError as e:
                    self.perror(f"Error opening file {statement.output_to}: {e}")
                    return False

            # Dispatch
            stop = super().onecmd(statement)
            return stop

        finally:
            if statement.output and self.stdout != saved_stdout:
                self.stdout.close()
                self.stdout = saved_stdout

    def default(self, line):
        """
        Called on an input line when the command prefix is not recognized.
        """
        self.perror(f"*** Unknown syntax: {line}")

    def do_help(self, arg):
        """
        Enhanced help command.
        """
        if arg:
            # Check if the command has an argparser
            func_name = 'do_' + arg
            if hasattr(self, func_name):
                func = getattr(self, func_name)
                if hasattr(func, 'argparser'):
                    func.argparser.print_help(file=self.stdout)
                    return
        
        super().do_help(arg)

    def run_transcript_tests(self, transcript_files):
        """
        Run transcript tests from a file.
        """
        if isinstance(transcript_files, str):
            transcript_files = [transcript_files]

        class TranscriptError(Exception):
            pass

        for file_path in transcript_files:
            with open(file_path, 'r') as f:
                content = f.read()

            # Simple regex parser for transcripts
            # Looks for (Cmd) command
            # Then captures output until next (Cmd) or EOF
            
            # Normalize newlines
            content = content.replace('\r\n', '\n')
            
            # Split by the prompt
            # Assuming standard prompt "(Cmd) "
            prompt_pattern = re.compile(r'^\(Cmd\) (.*)$', re.MULTILINE)
            
            pos = 0
            while True:
                match = prompt_pattern.search(content, pos)
                if not match:
                    break
                
                command_line = match.group(1).strip()
                start_output = match.end() + 1 # +1 for newline
                
                # Find next prompt to determine end of expected output
                next_match = prompt_pattern.search(content, start_output)
                if next_match:
                    end_output = next_match.start()
                else:
                    end_output = len(content)
                
                expected_output = content[start_output:end_output]
                # Strip trailing newlines from expectation for comparison
                expected_output = expected_output.strip()

                # Execute command
                capture = StdSim()
                old_stdout = self.stdout
                self.stdout = capture
                
                try:
                    self.onecmd(command_line)
                except Exception as e:
                    print(f"Exception during transcript: {e}")
                    traceback.print_exc()
                finally:
                    self.stdout = old_stdout
                
                actual_output = capture.getvalue().strip()
                
                # Normalize regex in expected output if present (simple check)
                # cmd2 supports regex in transcripts enclosed in /.../
                # Here we do simple string equality for the core requirement
                
                if expected_output != actual_output:
                    # Handle regex case if strictly required, otherwise strict match
                    # For this implementation, we assume strict match unless regex syntax is obvious
                    is_regex = expected_output.startswith('/') and expected_output.endswith('/')
                    if is_regex:
                        pattern = expected_output[1:-1]
                        if not re.search(pattern, actual_output, re.DOTALL):
                             raise TranscriptError(f"Regex mismatch in {file_path}.\nCmd: {command_line}\nExpected: {expected_output}\nActual: {actual_output}")
                    else:
                        raise TranscriptError(f"Output mismatch in {file_path}.\nCmd: {command_line}\nExpected:\n---\n{expected_output}\n---\nActual:\n---\n{actual_output}\n---")

                pos = end_output