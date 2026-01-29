from __future__ import annotations

import uuid as _uuid


def uuid() -> str:
    return _uuid.uuid4().hex