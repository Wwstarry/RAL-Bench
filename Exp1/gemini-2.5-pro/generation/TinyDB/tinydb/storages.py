import json
import os

class Storage:
    """
    Base class for all storages.
    A Storage object provides a simple key-value interface.
    """
    def read(self):
        """
        Read the entire database.

        :return: The database contents as a dictionary.
        """
        raise NotImplementedError

    def write(self, data):
        """
        Write the entire database.

        :param data: A dictionary to write to the database.
        """
        raise NotImplementedError

    def close(self):
        """
        Close the storage.
        """
        pass

class JSONStorage(Storage):
    """
    Stores the data in a JSON file.
    """
    def __init__(self, path, **kwargs):
        """
        Create a new instance.

        :param path: The path to the JSON file.
        :param kwargs: Keyword arguments passed to ``json.dump``.
        """
        self.path = path
        self._kwargs = kwargs
        # Create the file if it doesn't exist and is not in read-only mode
        if 'w' in kwargs.get('mode', 'w') or 'a' in kwargs.get('mode', 'w'):
             if not os.path.exists(self.path):
                with open(self.path, 'w') as f:
                    json.dump({}, f)

    def read(self):
        """
        Read data from the JSON file.
        """
        try:
            with open(self.path, 'r') as f:
                data = f.read()
                if not data:
                    return {}
                return json.loads(data)
        except (IOError, json.JSONDecodeError):
            # File does not exist or is empty/corrupted
            return {}

    def write(self, data):
        """
        Write data to the JSON file.
        """
        with open(self.path, 'w') as f:
            json.dump(data, f, **self._kwargs)

    def close(self):
        """
        No-op for file-based storage.
        """
        pass

    def __repr__(self):
        return f'<{type(self).__name__} path={self.path}>'