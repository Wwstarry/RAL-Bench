class ObservedWatch:
    def __init__(self, path, recursive):
        self._path = path
        self._recursive = recursive

    @property
    def path(self):
        return self._path

    @property
    def recursive(self):
        return self._recursive

    def __repr__(self):
        return "<ObservedWatch: path=%r, is_recursive=%r>" % (self.path, self.recursive)