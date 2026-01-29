from .generic import DictionaryObject, NameObject, NumberObject, ArrayObject, NullObject

class PageObject(DictionaryObject):
    def __init__(self, pdf=None):
        DictionaryObject.__init__(self)
        self.pdf = pdf

    @property
    def rotation(self):
        if "/Rotate" in self:
            return int(self["/Rotate"])
        return 0

    def rotate(self, angle):
        current_rotation = self.rotation
        new_rotation = (current_rotation + angle) % 360
        self[NameObject("/Rotate")] = NumberObject(new_rotation)
        return self

    def compress_content_streams(self):
        pass  # Stub for compatibility

    def extract_text(self):
        return "" # Stub