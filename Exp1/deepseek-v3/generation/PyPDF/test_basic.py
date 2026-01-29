#!/usr/bin/env python3
"""
Basic test script to verify the pypdf API compatibility.
"""

from pypdf import PdfReader, PdfWriter
import io

def test_basic_operations():
    # Test creating a PDF with a blank page
    writer = PdfWriter()
    page = writer.add_blank_page()
    page.rotate(90)
    
    # Write to memory
    output = io.BytesIO()
    writer.write(output)
    
    # Read it back
    output.seek(0)
    reader = PdfReader(output)
    
    # Verify page count and rotation
    assert len(reader.pages) == 1
    assert reader.pages[0].rotation == 90
    
    print("✓ Basic operations test passed")

def test_metadata():
    # Test metadata round-trip
    writer = PdfWriter()
    writer.add_blank_page()
    writer.add_metadata({"/Title": "Test Document", "/Author": "Test Author"})
    
    output = io.BytesIO()
    writer.write(output)
    
    output.seek(0)
    reader = PdfReader(output)
    
    assert reader.metadata.get("/Title") == "Test Document"
    assert reader.metadata.get("/Author") == "Test Author"
    
    print("✓ Metadata test passed")

def test_encryption():
    # Test encryption/decryption
    writer = PdfWriter()
    writer.add_blank_page()
    writer.encrypt("testpassword")
    
    output = io.BytesIO()
    writer.write(output)
    
    output.seek(0)
    reader = PdfReader(output)
    
    assert reader.is_encrypted == True
    assert reader.decrypt("testpassword") == True
    assert len(reader.pages) == 1
    
    print("✓ Encryption test passed")

def test_multipage():
    # Test multi-page document
    writer = PdfWriter()
    for i in range(3):
        page = writer.add_blank_page()
        page.rotate(i * 90)
    
    output = io.BytesIO()
    writer.write(output)
    
    output.seek(0)
    reader = PdfReader(output)
    
    assert len(reader.pages) == 3
    for i, page in enumerate(reader.pages):
        assert page.rotation == i * 90
    
    print("✓ Multi-page test passed")

if __name__ == "__main__":
    test_basic_operations()
    test_metadata()
    test_encryption()
    test_multipage()
    print("All tests passed!")