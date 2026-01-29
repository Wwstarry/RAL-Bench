"""
Minimal flow abstractions.

This module provides simplified flow objects compatible with import paths
used in mitmproxy addons. The implementation is intentionally lightweight
and does not perform any network or TLS operations.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional


class Flow:
    """
    A minimal base Flow.

    Attributes:
        id: Unique identifier for this flow instance.
        type: A string describing the flow type, e.g., "http".
        metadata: Arbitrary key-value metadata for addons to use.
        client_conn: Placeholder for a client connection object (None in this subset).
        server_conn: Placeholder for a server connection object (None in this subset).
    """

    def __init__(self, flow_type: str = "generic") -> None:
        self.id: str = str(uuid.uuid4())
        self.type: str = flow_type
        self.metadata: Dict[str, Any] = {}
        self.client_conn: Optional[Any] = None
        self.server_conn: Optional[Any] = None

    def __repr__(self) -> str:
        return f"<Flow id={self.id} type={self.type}>"

    def copy(self) -> "Flow":
        """
        Create a shallow copy of this flow. Data fields are shallow-copied,
        mutable values like metadata are copied to a new dict.
        """
        f = Flow(self.type)
        f.metadata = dict(self.metadata)
        f.client_conn = self.client_conn
        f.server_conn = self.server_conn
        return f