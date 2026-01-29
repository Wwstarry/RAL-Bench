import os
import json


class ID3:
    def __init__(self, path=None):
        self._frames = {}
        self._file_path = path
        if path and os.path.exists(path):
            self._load_frames()

    def _load_frames(self):
        with open(self._file_path, "r", encoding="utf-8") as f:
            self._frames = json.load(f)

    def add(self, frame):
        frame_id = frame.frame_id
        if frame_id not in self._frames:
            self._frames[frame_id] = []
        self._frames[frame_id].append(frame)

    def __getitem__(self, frame_id):
        if frame_id not in self._frames or not self._frames[frame_id]:
            raise KeyError(f"Frame ID '{frame_id}' not found.")
        return self._frames[frame_id][0]

    def getall(self, frame_id):
        return self._frames.get(frame_id, [])

    def delall(self, frame_id):
        if frame_id in self._frames:
            del self._frames[frame_id]

    def setall(self, frame_id, frames):
        self._frames[frame_id] = frames

    def save(self, path=None):
        save_path = path or self._file_path
        if not save_path:
            raise ValueError("No file path specified for saving.")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self._frames, f, ensure_ascii=False, indent=2)


class Frame:
    def __init__(self, encoding):
        self.encoding = encoding


class TIT2(Frame):
    frame_id = "TIT2"

    def __init__(self, encoding, text=None):
        super().__init__(encoding)
        self.text = text or []


class TPE1(Frame):
    frame_id = "TPE1"

    def __init__(self, encoding, text=None):
        super().__init__(encoding)
        self.text = text or []


class COMM(Frame):
    frame_id = "COMM"

    def __init__(self, encoding, lang, desc, text):
        super().__init__(encoding)
        self.lang = lang
        self.desc = desc
        self.text = text


class APIC(Frame):
    frame_id = "APIC"

    def __init__(self, encoding, mime, type, desc, data):
        super().__init__(encoding)
        self.mime = mime
        self.type = type
        self.desc = desc
        self.data = data