import shlex
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Statement:
    """Represents a parsed command statement."""
    command: str
    args: str
    argv: List[str]

class StatementParser:
    """Parser for command statements."""
    
    def parse(self, line: str) -> Statement:
        """Parse a command line into a Statement object."""
        if not line.strip():
            return Statement('', '', [])
        
        parts = shlex.split(line)
        command = parts[0] if parts else ''
        args = ' '.join(parts[1:]) if len(parts) > 1 else ''
        
        return Statement(
            command=command,
            args=args,
            argv=parts,
        )