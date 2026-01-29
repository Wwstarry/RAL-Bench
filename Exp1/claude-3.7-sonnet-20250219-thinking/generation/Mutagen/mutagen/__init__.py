"""Mutagen is a Python module to handle audio metadata."""

__version__ = "1.46.0"

class FileType:
    """Base class for audio file types."""
    
    filename = None
    
    def __init__(self, filename=None, *args, **kwargs):
        if filename is not None:
            self.load(filename, *args, **kwargs)
    
    def load(self, filename, *args, **kwargs):
        """Load metadata from a file."""
        raise NotImplementedError
    
    def save(self, filename=None, *args, **kwargs):
        """Save metadata to a file."""
        raise NotImplementedError
        
class MutagenError(Exception):
    """Base class for all exceptions in mutagen."""
    pass