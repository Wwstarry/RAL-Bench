import time
from typing import Any, Iterator, Optional

class Task:
    def __init__(self, description: str, total: Optional[float] = 100.0):
        self.description = description
        self.total = total
        self.completed = 0.0
        self._start_time = time.time()
        
    def update(self, advance: float = 1.0) -> None:
        """Update task progress."""
        self.completed = min(self.completed + advance, self.total or self.completed + advance)
        
    @property
    def percentage(self) -> float:
        """Get completion percentage."""
        if self.total and self.total > 0:
            return (self.completed / self.total) * 100
        return 0.0
        
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self._start_time

class Progress:
    def __init__(self, console=None):
        self.console = console
        self.tasks: list[Task] = []
        
    def add_task(self, description: str, total: Optional[float] = 100.0) -> int:
        """Add a new task and return its ID."""
        task = Task(description, total)
        self.tasks.append(task)
        return len(self.tasks) - 1
        
    def update(self, task_id: int, advance: float = 1.0) -> None:
        """Update a task's progress."""
        if 0 <= task_id < len(self.tasks):
            self.tasks[task_id].update(advance)
            
    def __iter__(self) -> Iterator[Any]:
        """Context manager interface."""
        return self
        
    def __enter__(self) -> "Progress":
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass
        
    def track(self, sequence, description: str = "Working...", total: Optional[float] = None) -> Iterator[Any]:
        """Track progress through an iterable."""
        if total is None:
            try:
                total = len(sequence)
            except TypeError:
                total = None
                
        task_id = self.add_task(description, total)
        
        for item in sequence:
            yield item
            self.update(task_id, 1.0)