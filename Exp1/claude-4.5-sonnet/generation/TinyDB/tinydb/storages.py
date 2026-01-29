"""
Storage backends for TinyDB
"""

import json
import os
from typing import Dict, Any
from abc import ABC, abstractmethod


class Storage(ABC):
    """
    Abstract base class for storage backends
    """
    
    @abstractmethod
    def read(self) -> Dict[str, Any]:
        """Read data from storage"""
        pass
    
    @abstractmethod
    def write(self, data: Dict[str, Any]):
        """Write data to storage"""
        pass


class JSONStorage(Storage):
    """
    JSON file-based storage backend
    """
    
    def __init__(self, path: str, create_dirs: bool = True, indent: int = 2):
        """
        Initialize JSON storage
        
        Args:
            path: Path to the JSON file
            create_dirs: Whether to create parent directories
            indent: JSON indentation level
        """
        self._path = path
        self._indent = indent
        
        if create_dirs:
            dirname = os.path.dirname(path)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)
        
        # Create file if it doesn't exist
        if not os.path.exists(path):
            with open(path, 'w') as f:
                json.dump({}, f)
    
    def read(self) -> Dict[str, Any]:
        """
        Read data from JSON file
        
        Returns:
            Dictionary containing all data
        """
        try:
            with open(self._path, 'r') as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def write(self, data: Dict[str, Any]):
        """
        Write data to JSON file
        
        Args:
            data: Dictionary to write
        """
        with open(self._path, 'w') as f:
            json.dump(data, f, indent=self._indent)


class MemoryStorage(Storage):
    """
    In-memory storage backend (for testing)
    """
    
    def __init__(self):
        """Initialize memory storage"""
        self._data: Dict[str, Any] = {}
    
    def read(self) -> Dict[str, Any]:
        """
        Read data from memory
        
        Returns:
            Dictionary containing all data
        """
        return self._data
    
    def write(self, data: Dict[str, Any]):
        """
        Write data to memory
        
        Args:
            data: Dictionary to write
        """
        self._data = data