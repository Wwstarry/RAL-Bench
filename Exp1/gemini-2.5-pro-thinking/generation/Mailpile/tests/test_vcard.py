from mailpile.vcard import VCardLine

def test_vcard_simple_line():
    """Test parsing a simple KEY:VALUE line."""
    line = "FN:John Doe"
    vcard_line = VCardLine(line)
    assert vcard_line.key == "FN"
    assert vcard_line.value == "John Doe"
    assert vcard_line.params == {}
    assert str(vcard_line) == line

def test_vcard_line_with_single_param():
    """Test parsing a line with one parameter."""
    line = "EMAIL;TYPE=INTERNET:johndoe@example.com"
    vcard_line = VCardLine(line)
    assert vcard_line.key == "EMAIL"
    assert vcard_line.value == "johndoe@example.com"
    assert vcard_line.params == {"TYPE": ["INTERNET"]}
    assert str(vcard_line) == line

def test_vcard_line_with_multiple_param_values():
    """Test parsing a parameter with multiple comma-separated values."""
    line = "TEL;TYPE=WORK,VOICE:+1-555-555-1234"
    vcard_line = VCardLine(line)
    assert vcard_line.key == "TEL"
    assert vcard_line.value == "+1-555-555-1234"
    assert vcard_line.params == {"TYPE": ["WORK", "VOICE"]}
    # Note: serialization might reorder params, but for one param it's stable.
    assert str(vcard_line) == line

def test_vcard_line_with_multiple_params():
    """Test parsing a line with multiple parameters."""
    line = "ADR;TYPE=HOME;LABEL=\"123 Main St\\nAnytown, USA\":;;123 Main St;Anytown;;;USA"
    vcard_line = VCardLine(line)
    assert vcard_line.key == "ADR"
    assert vcard_line.value == ";;123 Main St;Anytown;;;USA"
    assert vcard_line.params == {
        "TYPE": ["HOME"],
        "LABEL": ['"123 Main St\\nAnytown, USA"']
    }
    # Test serialization (note param order is not guaranteed)
    serialized = str(vcard_line)
    assert "ADR" in serialized
    assert "TYPE=HOME" in serialized
    assert "LABEL=\"123 Main St\\nAnytown, USA\"" in serialized
    assert vcard_line.value in serialized

def test_vcard_line_no_value():
    """Test parsing a line with no value part (e.g., BEGIN:VCARD)."""
    line = "BEGIN:VCARD"
    vcard_line = VCardLine(line)
    # Our simple parser puts the whole thing in the key if no colon
    assert vcard_line.key == "BEGIN:VCARD"
    assert vcard_line.value == ""
    assert vcard_line.params == {}