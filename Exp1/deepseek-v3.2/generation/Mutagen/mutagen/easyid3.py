import os
from typing import Dict, List, Optional, Union, Iterator, Tuple
from mutagen.id3 import ID3, TIT2, TPE1, COMM, APIC

class EasyID3:
    """High-level ID3 tag interface."""
    
    # Mapping from EasyID3 keys to ID3 frame IDs
    _key_to_frame = {
        'title': 'TIT2',
        'artist': 'TPE1',
        'album': 'TALB',
        'date': 'TDRC',
        'genre': 'TCON',
        'tracknumber': 'TRCK',
        'discnumber': 'TPOS',
        'comment': 'COMM',
    }
    
    # Reverse mapping
    _frame_to_key = {v: k for k, v in _key_to_frame.items()}
    
    def __init__(self, filename: Optional[str] = None):
        self._filename: Optional[str] = None
        self._data: Dict[str, List[str]] = {}
        
        if filename:
            self.load(filename)
    
    def load(self, filename: str) -> None:
        """Load tags from file."""
        self._filename = filename
        self._data.clear()
        
        try:
            id3 = ID3(filename)
            
            # Load text frames
            for frame_id, key in self._frame_to_key.items():
                if frame_id == 'COMM':
                    # Special handling for comments
                    for comm in id3.getall('COMM'):
                        if comm.desc == '':
                            self._data.setdefault(key, []).append(comm.text)
                elif frame_id in id3._frames:
                    for frame in id3.getall(frame_id):
                        self._data.setdefault(key, []).append(frame.text)
        except (IOError, KeyError):
            pass
    
    def __getitem__(self, key: str) -> List[str]:
        """Get values for key."""
        if key not in self._data:
            raise KeyError(key)
        return self._data[key].copy()
    
    def __setitem__(self, key: str, value: Union[str, List[str]]) -> None:
        """Set values for key."""
        if key not in self._key_to_frame:
            raise KeyError(f"Unknown key: {key}")
        
        if isinstance(value, str):
            value_list = [value]
        else:
            value_list = list(value)
        
        self._data[key] = value_list
    
    def __delitem__(self, key: str) -> None:
        """Delete key."""
        if key not in self._data:
            raise KeyError(key)
        del self._data[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._data
    
    def __len__(self) -> int:
        """Number of keys."""
        return len(self._data)
    
    def __iter__(self) -> Iterator[str]:
        """Iterate over keys."""
        return iter(self._data)
    
    def keys(self) -> Iterator[str]:
        """Get keys iterator."""
        return iter(self._data)
    
    def values(self) -> Iterator[List[str]]:
        """Get values iterator."""
        return iter(self._data.values())
    
    def items(self) -> Iterator[Tuple[str, List[str]]]:
        """Get items iterator."""
        return iter(self._data.items())
    
    def save(self, filename: Optional[str] = None) -> None:
        """Save tags to file."""
        save_filename = filename or self._filename
        if not save_filename:
            raise ValueError("No filename specified")
        
        # Create or load ID3 tag
        if os.path.exists(save_filename):
            id3 = ID3(save_filename)
        else:
            id3 = ID3()
        
        # Clear existing frames for our keys
        for frame_id in self._key_to_frame.values():
            id3.delall(frame_id)
        
        # Add frames for current data
        for key, values in self._data.items():
            frame_id = self._key_to_frame[key]
            
            if frame_id == 'COMM':
                # Special handling for comments
                for value in values:
                    comm = COMM(encoding=0, lang='eng', desc='', text=value)
                    id3.add(comm)
            else:
                # Text frames
                for value in values:
                    if frame_id == 'TIT2':
                        frame = TIT2(encoding=0, text=value)
                    elif frame_id == 'TPE1':
                        frame = TPE1(encoding=0, text=value)
                    else:
                        # Generic text frame
                        frame_class = type(frame_id, (TIT2,), {})
                        frame = frame_class(encoding=0, text=value)
                    id3.add(frame)
        
        # Save to file
        id3.save(save_filename)
        
        if not filename:
            self._filename = save_filename