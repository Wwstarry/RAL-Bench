"""
Minimal representation of the *Flow* abstraction known from mitmproxy.

The real implementation is **much** more sophisticated.  For the purpose
of the public-API tests we only model the attributes and APIs that are
actually being accessed by the test-suite.
"""
from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Flow:
    """
    The base class for any kind of recorded/captured flow
    (HTTP, TCP, WebSocket, …).

    Only a handful of attributes are implemented – just enough to satisfy
    import and attribute-access tests.
    """

    # Unique, stable identifier.
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # Human readable description (e.g. "http", "websocket", ...)
    type: str = "generic"
    # Timestamp when the flow object was first instantiated.
    timestamp_start: float = field(default_factory=lambda: datetime.datetime.utcnow().timestamp())
    # Arbitrary, user-provided metadata.
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:  # noqa: D401
        return f"<Flow {self.type} id={self.id}>"

    # ---------------------------------------------------------------------------------
    # Helper convenience APIs that exist on the real Flow object.  They are dummies here
    # but they help user code that is unaware of the stubbed nature of the library.
    # ---------------------------------------------------------------------------------
    def set_state(self, data: Dict[str, Any]) -> None:
        """
        Deserialize state into *this* instance.

        The stub implementation just copies the supplied data into
        `self.metadata`.
        """
        self.metadata.update(data)

    def get_state(self) -> Dict[str, Any]:
        """
        The counterpart of :py:meth:`set_state` – in the real code base
        this would serialize the full flow.  Here we only expose the
        metadata dictionary.
        """
        return dict(self.metadata)