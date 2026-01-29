from typing import Any, Dict, Optional, Tuple


class BaseBroker:
    def put_message(self, task_id: str, name: str, args: Tuple, kwargs: Dict) -> None:
        raise NotImplementedError
    
    def get_message(self) -> Optional[Tuple[str, str, Tuple, Dict]]:
        raise NotImplementedError