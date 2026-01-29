"""
Options management for mitmproxy.
"""

from typing import Optional, Any, Dict, List


class Options:
    """
    Options container for mitmproxy configuration.
    """
    
    def __init__(self, **kwargs):
        # Server options
        self.listen_host: str = kwargs.get("listen_host", "127.0.0.1")
        self.listen_port: int = kwargs.get("listen_port", 8080)
        self.mode: List[str] = kwargs.get("mode", ["regular"])
        
        # SSL/TLS options
        self.ssl_insecure: bool = kwargs.get("ssl_insecure", False)
        self.certs: List[str] = kwargs.get("certs", [])
        
        # Flow options
        self.flow_detail: int = kwargs.get("flow_detail", 1)
        self.showhost: bool = kwargs.get("showhost", False)
        
        # Dumper options
        self.flow_filter: Optional[str] = kwargs.get("flow_filter", None)
        self.save_stream_file: Optional[str] = kwargs.get("save_stream_file", None)
        
        # Script options
        self.scripts: List[str] = kwargs.get("scripts", [])
        
        # Verbosity
        self.verbosity: int = kwargs.get("verbosity", 0)
        
        # Additional options
        self._extra: Dict[str, Any] = {}
        for key, value in kwargs.items():
            if not hasattr(self, key):
                self._extra[key] = value
                
    def update(self, **kwargs) -> None:
        """Update options."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self._extra[key] = value
                
    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return self._extra.get(name)
        
    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_") or name in self.__dict__ or name in self.__class__.__dict__:
            object.__setattr__(self, name, value)
        else:
            if not hasattr(self, "_extra"):
                object.__setattr__(self, "_extra", {})
            self._extra[name] = value