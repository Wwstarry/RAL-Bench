import io

class OutputCapture:
    """
    Capture output written to it.
    """
    def __init__(self):
        self._buffer = io.StringIO()

    def write(self, text):
        self._buffer.write(text)

    def getvalue(self):
        return self._buffer.getvalue()

    def clear(self):
        self._buffer = io.StringIO()

    def flush(self):
        pass

class Transcript:
    """
    Transcript-based testing support.
    Run scripted commands and compare output line-by-line.
    """

    def __init__(self, cmd_instance):
        self.cmd = cmd_instance
        self.output_capture = OutputCapture()
        self.cmd.set_output_capture(self.output_capture)

    def run_script(self, script_lines):
        """
        Run a list of command lines, capturing output.
        Returns list of (command, output) tuples.
        """
        results = []
        for line in script_lines:
            line = line.rstrip('\n')
            if not line or line.startswith('#'):
                # Skip empty lines and comments
                continue
            self.output_capture.clear()
            ret = self.cmd.onecmd(line)
            output = self.output_capture.getvalue()
            results.append((line, output))
        return results

    def compare_transcript(self, script_lines, expected_outputs):
        """
        Run script_lines and compare outputs to expected_outputs line-by-line.
        expected_outputs is a list of strings.
        Returns True if all lines match, else False.
        """
        results = self.run_script(script_lines)
        for i, (cmd_line, output) in enumerate(results):
            expected = expected_outputs[i] if i < len(expected_outputs) else ''
            # Normalize line endings and strip trailing spaces
            out_lines = output.strip().splitlines()
            exp_lines = expected.strip().splitlines()
            if out_lines != exp_lines:
                return False
        return True