import shlex

class Statement(str):
    """
    String subclass that holds the parsed results of a command line.
    """
    def __new__(cls, value):
        return super().__new__(cls, value)

    def __init__(self, value):
        self.raw = value
        self.command = None
        self.args = None
        self.argv = []
        self.terminator = None
        self.suffix = None
        self.pipe_to = None
        self.output = None
        self.output_to = None
        
        self._parse()

    def _parse(self):
        # Basic parsing logic to emulate cmd2 behavior
        # 1. Check for redirection
        # 2. Split command and args
        
        raw_input = self.raw.strip()
        
        # Handle simple output redirection > and >>
        # This is a simplified parser compared to full cmd2 but covers core API
        if '>>' in raw_input:
            parts = raw_input.split('>>')
            self.output = '>>'
            self.output_to = parts[-1].strip()
            raw_input = '>>'.join(parts[:-1]).strip()
        elif '>' in raw_input:
            parts = raw_input.split('>')
            self.output = '>'
            self.output_to = parts[-1].strip()
            raw_input = '>'.join(parts[:-1]).strip()

        try:
            self.argv = shlex.split(raw_input)
        except ValueError:
            self.argv = raw_input.split()

        if self.argv:
            self.command = self.argv[0]
            if len(self.argv) > 1:
                # Reconstruct args string roughly
                # In a real implementation, we would slice the raw string based on indices
                self.args = raw_input[len(self.command):].strip()
            else:
                self.args = ''
        else:
            self.command = ''
            self.args = ''

def parse_statement(line):
    return Statement(line)