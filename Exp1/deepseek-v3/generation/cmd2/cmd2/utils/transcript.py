from typing import List

class Transcript:
    """Records and plays back command transcripts for testing."""
    
    def __init__(self):
        self._commands: List[str] = []
        self._outputs: List[str] = []
    
    def record_command(self, command: str) -> None:
        """Record a command in the transcript."""
        self._commands.append(command)
    
    def record_output(self, output: str) -> None:
        """Record command output in the transcript."""
        self._outputs.append(output)
    
    def verify(self, expected_commands: List[str], expected_outputs: List[str]) -> bool:
        """Verify transcript matches expected commands and outputs."""
        return (
            self._commands == expected_commands and
            self._outputs == expected_outputs
        )