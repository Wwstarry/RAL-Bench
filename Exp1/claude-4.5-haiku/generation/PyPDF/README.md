# pypdf

A pure Python PDF manipulation library that provides API compatibility with the core parts of the pypdf project.

## Features

- Read PDF files and extract pages
- Write PDF files with multiple pages
- Rotate pages
- Add metadata to documents
- Basic encryption support
- Merge and split PDFs

## Installation

```bash
pip install -e .
```

## Usage

### Reading a PDF

```python
from pypdf import PdfReader

reader = PdfReader("example.pdf")
for page in reader.pages:
    print(page.rotation)
```

### Writing a PDF

```python
from pypdf import PdfWriter

writer = PdfWriter()
writer.add_blank_page(width=612, height=792)
writer.write("output.pdf")
```

### Copying pages

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

writer.write("output.pdf")
```

### Adding metadata

```python
from pypdf import PdfWriter

writer = PdfWriter()
writer.add_metadata({
    "/Title": "My Document",
    "/Author": "John Doe"
})
writer.write("output.pdf")
```

### Encryption

```python
from pypdf import PdfReader, PdfWriter

# Write encrypted PDF
writer = PdfWriter()
writer.add_blank_page()
writer.encrypt("password123")
writer.write("encrypted.pdf")

# Read encrypted PDF
reader = PdfReader("encrypted.pdf")
if reader.is_encrypted:
    reader.decrypt("password123")
```

## API Reference

### PdfReader

- `__init__(stream)` - Initialize reader from file path, bytes, or file-like object
- `pages` - List of PageObject instances
- `is_encrypted` - Boolean indicating if PDF is encrypted
- `decrypt(password)` - Decrypt the PDF
- `metadata` - Dictionary of document metadata

### PdfWriter

- `__init__()` - Initialize writer
- `add_page(page)` - Add a page from a reader
- `add_blank_page(width, height)` - Add a blank page
- `add_metadata(metadata)` - Add document metadata
- `encrypt(password)` - Encrypt the PDF
- `write(file_obj)` - Write PDF to file

### PageObject

- `rotate(angle)` - Rotate page by angle (0, 90, 180, 270)
- `rotation` - Get current rotation angle