import time
import sys
from typing import Iterable, List, Optional
from .console import Console
from .text import Text

class TaskID(int):
    pass

class Task:
    def __init__(self, id: TaskID, description: str, total: float, completed: float = 0):
        self.id = id
        self.description = description
        self.total = total
        self.completed = completed
        self.finished = False

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.completed / self.total) * 100

class Progress:
    def __init__(self, console: Console = None, auto_refresh: bool = True, transient: bool = False):
        self.console = console or Console()
        self.tasks: List[Task] = []
        self._task_index = 0
        self.auto_refresh = auto_refresh
        self.transient = transient
        self._started = False

    def add_task(self, description: str, total: float = 100, start: bool = True) -> TaskID:
        task_id = TaskID(self._task_index)
        self._task_index += 1
        task = Task(task_id, description, total)
        self.tasks.append(task)
        return task_id

    def update(self, task_id: TaskID, advance: float = None, completed: float = None, description: str = None):
        for task in self.tasks:
            if task.id == task_id:
                if completed is not None:
                    task.completed = completed
                if advance is not None:
                    task.completed += advance
                if description is not None:
                    task.description = description
                
                if task.completed >= task.total:
                    task.completed = task.total
                    task.finished = True
        self.refresh()

    def start(self):
        self._started = True
        self.console.file.write("\n" * len(self.tasks)) # Allocate space
        self.refresh()

    def stop(self):
        self._started = False
        if self.transient:
            # Move cursor up and clear
            self.console.file.write(f"\033[{len(self.tasks)}A\033[J")
        self.console.file.write("\n")

    def refresh(self):
        if not self._started:
            return
        
        # Move cursor up N lines
        n_lines = len(self.tasks)
        if n_lines > 0:
            self.console.file.write(f"\033[{n_lines}A")
        
        for task in self.tasks:
            # Render bar
            width = 30
            percent = task.percentage / 100.0
            filled = int(width * percent)
            bar = "█" * filled + " " * (width - filled)
            
            color = "32" if task.finished else "34" # Green if done, Blue otherwise
            
            line = f"\r\033[K{task.description} [\033[{color}m{bar}\033[0m] {int(task.percentage)}%"
            self.console.file.write(line + "\n")
        
        self.console.file.flush()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

def track(sequence: Iterable, description: str = "Working...", total: float = None):
    if total is None:
        try:
            total = len(sequence)
        except TypeError:
            total = 100 # Fallback

    with Progress() as progress:
        task_id = progress.add_task(description, total=total)
        for item in sequence:
            yield item
            progress.update(task_id, advance=1)