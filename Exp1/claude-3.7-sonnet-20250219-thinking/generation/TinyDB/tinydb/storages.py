import json
import os
from typing import Dict, Any

class JSONStorage:
    """
    Storage for JSON files.
    """
    
    def __init__(self, path: str, create_dirs=False, encoding=None, **kwargs):
        """
        Initialize a JSONStorage instance.
        
        Args:
            path: Path to the JSON file.
            create_dirs: Whether to create missing directories.
            encoding: The encoding to use.
            **kwargs: Additional arguments for json.dump.
        """
        self.kwargs = kwargs
        self._handle = None
        
        if path is None:
            raise ValueError("path cannot be None")
        
        self.path = os.path.abspath(path)
        
        if create_dirs:
            base_dir = os.path.dirname(self.path)
            if not os.path.exists(base_dir):
                os.makedirs(base_dir)
        
        # Create the file if it doesn't exist
        if not os.path.exists(self.path):
            with open(self.path, 'w', encoding=encoding) as f:
                json.dump({}, f)
        
        self.encoding = encoding
    
    def read(self) -> Dict:
        """
        Read data from the storage.
        
        Returns:
            The data from the JSON file.
        """
        with open(self.path, 'r', encoding=self.encoding) as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    
    def write(self, data: Dict) -> None:
        """
        Write data to the storage.
        
        Args:
            data: The data to write.
        """
        with open(self.path, 'w', encoding=self.encoding) as f:
            json.dump(data, f, **self.kwargs)
    
    def close(self) -> None:
        """
        Close the storage.
        """
        if self._handle is not None:
            self._handle.close()
            self._handle = None