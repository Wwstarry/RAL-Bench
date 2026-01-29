import os
from mutagen.id3 import ID3, TIT2, TPE1, COMM, APIC

class EasyID3(dict):
    """EasyID3 interface for ID3 tags."""
    
    _mapping = {
        'title': 'TIT2',
        'artist': 'TPE1',
        'comment': 'COMM',
    }
    
    def __init__(self, filename=None):
        super().__init__()
        self._filename = filename
        self._id3 = ID3()
        
        if filename is not None and os.path.exists(filename):
            self._id3 = ID3(filename)
            self._load()
    
    def _load(self):
        for key, frame_id in self._mapping.items():
            frames = self._id3.getall(frame_id)
            if frames:
                if frame_id == 'COMM':
                    self[key] = [frame.text for frame in frames]
                else:
                    self[key] = [frame.text for frame in frames]
    
    def __setitem__(self, key, value):
        if key not in self._mapping:
            raise KeyError(f"{key} is not a valid key")
        if not isinstance(value, list):
            value = [value]
        super().__setitem__(key, value)
    
    def save(self, filename=None):
        """Save tags to file."""
        target = filename or self._filename
        if target is None:
            raise ValueError("No filename specified")
        
        # Update ID3 frames from our dict
        for key, frame_id in self._mapping.items():
            if key in self:
                frames = []
                if frame_id == 'COMM':
                    for text in self[key]:
                        frames.append(COMM(encoding=3, lang='eng', desc='', text=text))
                else:
                    for text in self[key]:
                        if frame_id == 'TIT2':
                            frames.append(TIT2(encoding=3, text=text))
                        elif frame_id == 'TPE1':
                            frames.append(TPE1(encoding=3, text=text))
                self._id3.setall(frame_id, frames)
            else:
                self._id3.delall(frame_id)
        
        self._id3.save(target)
        if filename is not None:
            self._filename = filename