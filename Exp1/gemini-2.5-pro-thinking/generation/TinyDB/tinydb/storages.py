import json
import os

class Storage:
    """
    Abstract base class for storages.
    """
    def read(self):
        raise NotImplementedError

    def write(self, data):
        raise NotImplementedError

    def close(self):
        pass

class JSONStorage(Storage):
    """
    Stores data in a JSON file.
    """
    def __init__(self, path, **kwargs):
        self._path = os.path.abspath(path)
        
        # Default kwargs for json.dump
        kwargs.setdefault('indent', 4)
        kwargs.setdefault('sort_keys', True)
        kwargs.setdefault('separators', (',', ': '))
        self._kwargs = kwargs
        
        # Create directory if it doesn't exist
        dir_path = os.path.dirname(self._path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # Create file if it doesn't exist
        if not os.path.exists(self._path):
            with open(self._path, 'w') as f:
                json.dump({}, f)

    def read(self):
        try:
            with open(self._path, 'r') as f:
                data = f.read()
                if not data:
                    return {}
                return json.loads(data)
        except (IOError, json.JSONDecodeError):
            return {}

    def write(self, data):
        # Use atomic write to prevent data corruption
        temp_path = self._path + '.tmp'
        with open(temp_path, 'w') as f:
            json.dump(data, f, **self._kwargs)
        
        # On some systems, os.rename will fail if the destination file exists.
        if os.path.exists(self._path):
            try:
                os.remove(self._path)
            except OSError:
                pass # May fail on Windows if the file is in use
        
        os.rename(temp_path, self._path)

    def close(self):
        # No file handle is kept open, so nothing to do
        pass