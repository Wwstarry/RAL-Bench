from typing import Dict, Optional


class TaskRegistry:
    def __init__(self):
        self._tasks: Dict[str, any] = {}
    
    def register(self, task: any) -> None:
        self._tasks[task.name] = task
    
    def get(self, name: str) -> Optional[any]:
        return self._tasks.get(name)
    
    def unregister(self, name: str) -> None:
        if name in self._tasks:
            del self._tasks[name]