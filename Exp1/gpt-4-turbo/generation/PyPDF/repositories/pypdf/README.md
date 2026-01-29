# pypdf

Pure Python PDF manipulation library (API-compatible with core pypdf).

## Usage

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()
for page in reader.pages:
    writer.add_page(page)
writer.write(open("output.pdf", "wb"))
```