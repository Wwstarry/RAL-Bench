import json
import os

class Storage:
    """Abstract base class for storage."""
    def read(self):
        raise NotImplementedError

    def write(self, data):
        raise NotImplementedError

class JSONStorage(Storage):
    """
    Store data in a JSON file.
    """
    def __init__(self, path):
        self.path = path
        self._ensure_file()

    def _ensure_file(self):
        """Create the file if it doesn't exist."""
        if not os.path.exists(self.path):
            with open(self.path, 'w') as f:
                json.dump({}, f)

    def read(self):
        """Read the whole database from the file."""
        try:
            with open(self.path, 'r') as f:
                # Handle empty files
                content = f.read()
                if not content:
                    return {}
                return json.loads(content)
        except (ValueError, json.JSONDecodeError):
            return {}

    def write(self, data):
        """Write the whole database to the file."""
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=4)