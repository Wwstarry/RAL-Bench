"""
Base broker class
"""

from typing import Any, Dict, Optional


class BaseBroker:
    """Base class for message brokers"""
    
    def publish(self, message: Dict[str, Any]):
        """Publish a task message"""
        raise NotImplementedError()
    
    def consume(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Consume a task message"""
        raise NotImplementedError()