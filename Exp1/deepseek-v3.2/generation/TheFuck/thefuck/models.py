class Command:
    def __init__(self, script, stdout='', stderr='', return_code=1):
        self.script = script
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
    
    @classmethod
    def from_raw_script(cls, script, stdout='', stderr='', return_code=1):
        return cls(script, stdout, stderr, return_code)
    
    def __repr__(self):
        return f"Command(script={self.script!r}, return_code={self.return_code})"

class CorrectedCommand:
    def __init__(self, script, side_effect=None, priority=100):
        self.script = script
        self.side_effect = side_effect
        self.priority = priority
    
    def __repr__(self):
        return f"CorrectedCommand(script={self.script!r}, priority={self.priority})"