"""
PDF object types and utilities.
"""

from typing import Any, Dict, List, Optional, Union


class PDFObject:
    """Base class for PDF objects."""

    def __init__(self, value: Any = None):
        self.value = value


class DictionaryObject(PDFObject, dict):
    """Represents a PDF dictionary."""

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        PDFObject.__init__(self)


class ArrayObject(PDFObject, list):
    """Represents a PDF array."""

    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        PDFObject.__init__(self)


class TextStringObject(PDFObject, str):
    """Represents a PDF text string."""

    def __new__(cls, value: str):
        return str.__new__(cls, value)


class NameObject(PDFObject, str):
    """Represents a PDF name."""

    def __new__(cls, value: str):
        return str.__new__(cls, value)


class NumberObject(PDFObject, (int, float)):
    """Represents a PDF number."""

    def __new__(cls, value: Union[int, float]):
        if isinstance(value, float):
            return float.__new__(cls, value)
        else:
            return int.__new__(cls, value)


class NullObject(PDFObject):
    """Represents a PDF null object."""

    def __repr__(self) -> str:
        return "null"


class IndirectObject(PDFObject):
    """Represents an indirect object reference."""

    def __init__(self, obj_num: int, gen_num: int = 0):
        super().__init__()
        self.obj_num = obj_num
        self.gen_num = gen_num

    def __repr__(self) -> str:
        return f"{self.obj_num} {self.gen_num} R"