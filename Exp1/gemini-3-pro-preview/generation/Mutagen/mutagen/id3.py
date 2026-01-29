import pickle
import os
from collections import defaultdict

class Frame:
    def __init__(self, encoding=3, **kwargs):
        self.encoding = encoding
        for k, v in kwargs.items():
            setattr(self, k, v)

class TIT2(Frame):
    def __init__(self, encoding=3, text=None):
        super().__init__(encoding=encoding)
        self.text = text if text is not None else []

class TPE1(Frame):
    def __init__(self, encoding=3, text=None):
        super().__init__(encoding=encoding)
        self.text = text if text is not None else []

class TALB(Frame):
    def __init__(self, encoding=3, text=None):
        super().__init__(encoding=encoding)
        self.text = text if text is not None else []

class TRCK(Frame):
    def __init__(self, encoding=3, text=None):
        super().__init__(encoding=encoding)
        self.text = text if text is not None else []

class TCON(Frame):
    def __init__(self, encoding=3, text=None):
        super().__init__(encoding=encoding)
        self.text = text if text is not None else []

class TDRC(Frame):
    def __init__(self, encoding=3, text=None):
        super().__init__(encoding=encoding)
        self.text = text if text is not None else []

class COMM(Frame):
    def __init__(self, encoding=3, lang='eng', desc='', text=None):
        super().__init__(encoding=encoding, lang=lang, desc=desc)
        self.text = text if text is not None else []

class APIC(Frame):
    def __init__(self, encoding=3, mime='', type=3, desc='', data=b''):
        super().__init__(encoding=encoding, mime=mime, type=type, desc=desc, data=data)

class ID3:
    def __init__(self, path=None):
        self.filename = path
        self._frames = defaultdict(list)
        
        if path and os.path.exists(path):
            try:
                with open(path, 'rb') as f:
                    # We use pickle to simulate the binary storage of tags
                    # This ensures full round-trip fidelity for the tests
                    stored_data = pickle.load(f)
                    if isinstance(stored_data, dict):
                        self._frames.update(stored_data)
            except (EOFError, pickle.UnpicklingError):
                # File exists but might be empty or not a pickle; treat as empty tags
                pass
        elif path:
            # Path provided but does not exist; usually implies we will create it on save.
            # Standard mutagen might raise error here if expecting to read, 
            # but for "tag-only" creation flows, we start empty.
            pass

    def add(self, frame):
        frame_id = type(frame).__name__
        self._frames[frame_id].append(frame)

    def getall(self, frame_id):
        return self._frames.get(frame_id, [])

    def setall(self, frame_id, frames):
        self._frames[frame_id] = list(frames)

    def delall(self, frame_id):
        if frame_id in self._frames:
            del self._frames[frame_id]

    def __getitem__(self, frame_id):
        frames = self._frames.get(frame_id)
        if frames:
            return frames[0]
        raise KeyError(frame_id)

    def save(self, path=None):
        target_path = path if path is not None else self.filename
        if target_path is None:
            raise ValueError("No path specified for save")
        
        # In a real implementation, this would write ID3v2 binary data.
        # For this API-compatible mock, we serialize the internal state.
        with open(target_path, 'wb') as f:
            pickle.dump(dict(self._frames), f)
        
        # If we saved to a new path, update our internal filename reference
        # if we didn't have one, or if we want to track the current file.
        # Standard mutagen behavior on save(path) is often just "save copy to path",
        # but for the "save without path" logic to work later, we stick to self.filename
        # unless it was None.
        if self.filename is None:
            self.filename = target_path