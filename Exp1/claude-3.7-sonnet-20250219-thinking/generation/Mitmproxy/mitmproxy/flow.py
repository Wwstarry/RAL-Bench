"""
Base flow abstractions.
"""
from typing import Optional, Dict, Any, List


class Flow:
    """
    Base class for all flows.
    """
    def __init__(self):
        self.id: str = ""
        self.client_conn = None
        self.server_conn = None
        self.error: Optional[str] = None
        self.marked: bool = False
        self.metadata: Dict[str, Any] = {}
        self.comment: str = ""
        self.intercepted: bool = False
        self._backup: Dict[str, Any] = {}

    def copy(self):
        """Create a copy of this flow."""
        return Flow()

    def modified(self) -> bool:
        """
        Has this flow been modified?
        """
        return False

    def backup(self) -> None:
        """
        Back up flow data.
        """
        self._backup = {}

    def revert(self) -> None:
        """
        Revert to backed up state.
        """
        if self._backup:
            self._backup = {}

    def kill(self) -> None:
        """
        Kill this flow.
        """
        pass

    def intercept(self) -> None:
        """
        Intercept this flow.
        """
        self.intercepted = True

    def resume(self) -> None:
        """
        Resume this flow.
        """
        self.intercepted = False