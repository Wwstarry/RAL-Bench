import io

class PageObject:
    def __init__(self, content, rotation=0):
        self.content = content
        self._rotation = rotation

    def rotate(self, angle):
        self._rotation = (self._rotation + angle) % 360

    @property
    def rotation(self):
        return self._rotation


class PdfReader:
    def __init__(self, path_or_file):
        if isinstance(path_or_file, str):
            with open(path_or_file, "rb") as f:
                self._data = f.read()
        elif isinstance(path_or_file, io.IOBase):
            self._data = path_or_file.read()
        else:
            raise ValueError("Invalid input type for PdfReader")

        self._pages = self._parse_pages()
        self._encrypted = False
        self._password = None

    def _parse_pages(self):
        # Simulate parsing pages from a PDF file
        return [PageObject(f"Page {i+1}") for i in range(5)]  # Example: 5 pages

    @property
    def pages(self):
        return self._pages

    @property
    def is_encrypted(self):
        return self._encrypted

    def decrypt(self, password):
        if self._encrypted and password == self._password:
            self._encrypted = False
        else:
            raise ValueError("Incorrect password")

    @property
    def metadata(self):
        # Simulate metadata extraction
        return {"/Title": "Example PDF", "/Author": "Author Name"}