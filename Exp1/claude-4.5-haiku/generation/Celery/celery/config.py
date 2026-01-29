from typing import Any, Dict, Optional


class Config:
    def __init__(self):
        self._config: Dict[str, Any] = {
            "broker_url": "memory://",
            "result_backend": "memory://",
            "task_always_eager": False,
            "task_eager_propagates": True,
            "task_serializer": "json",
            "result_serializer": "json",
            "accept_content": ["json"],
            "timezone": "UTC",
            "enable_utc": True,
        }
    
    def __getattr__(self, key: str) -> Any:
        if key.startswith("_"):
            return object.__getattribute__(self, key)
        return self._config.get(key)
    
    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_"):
            object.__setattr__(self, key, value)
        else:
            self._config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        self._config.update(config_dict)