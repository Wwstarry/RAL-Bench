import io

class PdfWriter:
    def __init__(self):
        self._pages = []
        self._metadata = {}
        self._encrypted = False
        self._password = None

    def add_page(self, page):
        if not isinstance(page, PageObject):
            raise ValueError("Invalid page object")
        self._pages.append(page)

    def add_blank_page(self, width, height):
        blank_page = PageObject(f"Blank page ({width}x{height})")
        self._pages.append(blank_page)

    def write(self, file_obj):
        if isinstance(file_obj, str):
            with open(file_obj, "wb") as f:
                f.write(self._generate_pdf())
        elif isinstance(file_obj, io.IOBase):
            file_obj.write(self._generate_pdf())
        else:
            raise ValueError("Invalid file object")

    def _generate_pdf(self):
        # Simulate PDF generation
        pdf_content = b"%PDF-1.4\n"
        for i, page in enumerate(self._pages):
            pdf_content += f"Page {i+1}: {page.content}, Rotation: {page.rotation}\n".encode()
        if self._encrypted:
            pdf_content += b"Encrypted\n"
        return pdf_content

    def encrypt(self, password):
        self._encrypted = True
        self._password = password

    def add_metadata(self, mapping):
        self._metadata.update(mapping)