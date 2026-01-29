class PageObject:
    def __init__(self, reader, dictionary):
        self._reader = reader
        self._dictionary = dictionary
        self._rotation = self._dictionary.get(b"/Rotate", 0)
        if isinstance(self._rotation, list):
            # Defensive: if rotation is an array, take first element
            self._rotation = self._rotation[0] if self._rotation else 0
        if not isinstance(self._rotation, int):
            try:
                self._rotation = int(self._rotation)
            except Exception:
                self._rotation = 0

    def rotate(self, angle: int):
        angle = angle % 360
        self._rotation = (self._rotation + angle) % 360
        self._dictionary[b"/Rotate"] = self._rotation

    @property
    def rotation(self) -> int:
        return self._rotation

    def __repr__(self):
        return f"<PageObject rotation={self._rotation}>"