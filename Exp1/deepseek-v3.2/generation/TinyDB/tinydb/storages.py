"""
Storage module for TinyDB.
"""
import json
import os
from typing import Dict, List, Any
from abc import ABC, abstractmethod


class Storage(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def read(self) -> Dict[str, List[Dict]]:
        """Read all data from storage."""
        pass
    
    @abstractmethod
    def write(self, data: Dict[str, List[Dict]]) -> None:
        """Write all data to storage."""
        pass
    
    def _sync_table(self, table_name: str, data: List[Dict]) -> None:
        """
        Sync a single table to storage.
        
        Args:
            table_name: Name of the table
            data: Table data
        """
        all_data = self.read()
        all_data[table_name] = data
        self.write(all_data)


class JSONStorage(Storage):
    """JSON file storage backend."""
    
    def __init__(self, path: str):
        """
        Initialize JSON storage.
        
        Args:
            path: Path to JSON file
        """
        self.path = path
    
    def read(self) -> Dict[str, List[Dict]]:
        """Read data from JSON file."""
        if not os.path.exists(self.path):
            return {}
        
        try:
            with open(self.path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def write(self, data: Dict[str, List[Dict]]) -> None:
        """Write data to JSON file."""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        
        with open(self.path, 'w') as f:
            json.dump(data, f, indent=2)