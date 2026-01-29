from typing import Any, Dict, Optional, Tuple


class BaseBackend:
    def set_result(self, task_id: str, result: Any, state: str) -> None:
        raise NotImplementedError
    
    def get_result(self, task_id: str) -> Tuple[str, Any]:
        raise NotImplementedError