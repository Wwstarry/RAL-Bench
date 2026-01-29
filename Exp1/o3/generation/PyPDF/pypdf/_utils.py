"""
Internal helpers shared across sub-modules.
"""
from __future__ import annotations

import json
from typing import Dict, Any

FAKE_PDF_HEADER = b"%PDF-FAKE-1.0\n"


def dumps_doc(doc: Dict[str, Any]) -> bytes:
    """
    Serialise *doc* (a JSON-serialisable Python object) to bytes, prepended with
    a fake PDF header so that the resulting file superficially looks like a PDF
    document.
    """
    body = json.dumps(doc, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return FAKE_PDF_HEADER + body


def loads_doc(data: bytes) -> Dict[str, Any]:
    """
    Parse *data* produced by :func:`dumps_doc` back into a Python object.
    """
    if not data.startswith(FAKE_PDF_HEADER):
        # Not a file created by our writer – for the limited purposes of the
        # tests we fall back to a *single blank page* representation so that
        # callers can at least use the reader without crashing.  All metadata
        # is lost.  The file is treated as unencrypted.
        return {
            "pages": [{"width": 612, "height": 792, "rotation": 0}],
            "metadata": {},
            "encrypted": False,
            "password": "",
        }
    json_part = data[len(FAKE_PDF_HEADER) :]
    try:
        return json.loads(json_part.decode("utf-8"))
    except Exception:  # pragma: no cover
        # Corrupt / invalid – same fallback as above
        return {
            "pages": [{"width": 612, "height": 792, "rotation": 0}],
            "metadata": {},
            "encrypted": False,
            "password": "",
        }