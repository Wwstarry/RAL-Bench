"""Progress bars and task tracking."""

from typing import Optional, Any, Iterable, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
import time


@dataclass
class Task:
    """A progress task."""
    
    id: int
    description: str
    total: Optional[float] = None
    completed: float = 0.0
    visible: bool = True
    fields: dict = field(default_factory=dict)
    start_time: Optional[float] = None
    stop_time: Optional[float] = None
    finished_time: Optional[float] = None
    
    @property
    def finished(self) -> bool:
        """Check if task is finished."""
        if self.total is None:
            return False
        return self.completed >= self.total
    
    @property
    def percentage(self) -> float:
        """Get completion percentage."""
        if self.total is None or self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100.0
    
    @property
    def elapsed(self) -> Optional[float]:
        """Get elapsed time."""
        if self.start_time is None:
            return None
        end_time = self.stop_time or time.time()
        return end_time - self.start_time


class Progress:
    """Progress bar manager."""

    def __init__(
        self,
        *columns: Any,
        console: Optional[Any] = None,
        auto_refresh: bool = True,
        refresh_per_second: float = 10,
        speed_estimate_period: float = 30.0,
        transient: bool = False,
        redirect_stdout: bool = True,
        redirect_stderr: bool = True,
        get_time: Optional[Callable[[], float]] = None,
        disable: bool = False,
        expand: bool = False,
    ) -> None:
        self.columns = columns
        self.console = console
        self.auto_refresh = auto_refresh
        self.refresh_per_second = refresh_per_second
        self.speed_estimate_period = speed_estimate_period
        self.transient = transient
        self.redirect_stdout = redirect_stdout
        self.redirect_stderr = redirect_stderr
        self.get_time = get_time or time.time
        self.disable = disable
        self.expand = expand
        
        self._tasks: List[Task] = []
        self._task_counter = 0
        self._started = False

    def __enter__(self) -> "Progress":
        """Enter context manager."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        self.stop()

    def start(self) -> None:
        """Start the progress display."""
        self._started = True

    def stop(self) -> None:
        """Stop the progress display."""
        self._started = False

    def add_task(
        self,
        description: str,
        start: bool = True,
        total: Optional[float] = 100.0,
        completed: float = 0,
        visible: bool = True,
        **fields: Any,
    ) -> int:
        """Add a new task."""
        task_id = self._task_counter
        self._task_counter += 1
        
        task = Task(
            id=task_id,
            description=description,
            total=total,
            completed=completed,
            visible=visible,
            fields=fields,
            start_time=self.get_time() if start else None,
        )
        
        self._tasks.append(task)
        return task_id

    def update(
        self,
        task_id: int,
        *,
        total: Optional[float] = None,
        completed: Optional[float] = None,
        advance: Optional[float] = None,
        description: Optional[str] = None,
        visible: Optional[bool] = None,
        refresh: bool = False,
        **fields: Any,
    ) -> None:
        """Update a task."""
        task = self._get_task(task_id)
        
        if total is not None:
            task.total = total
        if completed is not None:
            task.completed = completed
        if advance is not None:
            task.completed += advance
        if description is not None:
            task.description = description
        if visible is not None:
            task.visible = visible
        
        task.fields.update(fields)
        
        # Check if task is finished
        if task.total is not None and task.completed >= task.total:
            if task.finished_time is None:
                task.finished_time = self.get_time()

    def advance(self, task_id: int, advance: float = 1.0) -> None:
        """Advance a task."""
        self.update(task_id, advance=advance)

    def _get_task(self, task_id: int) -> Task:
        """Get a task by ID."""
        for task in self._tasks:
            if task.id == task_id:
                return task
        raise KeyError(f"Task {task_id} not found")

    def track(
        self,
        sequence: Iterable[Any],
        total: Optional[float] = None,
        task_id: Optional[int] = None,
        description: str = "Working...",
        update_period: float = 0.1,
    ) -> Iterable[Any]:
        """Track progress of an iterable."""
        if task_id is None:
            # Try to get length of sequence
            try:
                total = total or len(sequence)  # type: ignore
            except (TypeError, AttributeError):
                total = None
            
            task_id = self.add_task(description, total=total)
        
        for item in sequence:
            yield item
            self.advance(task_id)

    @property
    def tasks(self) -> List[Task]:
        """Get all tasks."""
        return self._tasks.copy()

    def get_task(self, task_id: int) -> Task:
        """Get a task by ID."""
        return self._get_task(task_id)