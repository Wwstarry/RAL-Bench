import time
from typing import List, Optional, Dict, Any

class Task:
    def __init__(self, description: str, total: int = 100, completed: int = 0, visible: bool = True):
        self.description = description
        self.total = total
        self.completed = completed
        self.visible = visible

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return min(100.0, (self.completed / self.total) * 100)

    def advance(self, n: int = 1):
        self.completed = min(self.total, self.completed + n)

class Progress:
    def __init__(self, auto_refresh: bool = False, width: int = 40):
        self.tasks: List[Task] = []
        self.auto_refresh = auto_refresh
        self.width = width

    def add_task(self, description: str, total: int = 100, completed: int = 0, visible: bool = True) -> Task:
        task = Task(description, total, completed, visible)
        self.tasks.append(task)
        return task

    def update(self, task: Task, advance: int = 1):
        task.advance(advance)
        if self.auto_refresh:
            self.refresh()

    def refresh(self):
        print(self.__rich__(), end="")

    def __rich__(self) -> str:
        out = ""
        for task in self.tasks:
            if not task.visible:
                continue
            bar_width = self.width - 20
            pct = task.percentage
            filled = int(bar_width * pct / 100)
            bar = "█" * filled + "░" * (bar_width - filled)
            out += f"{task.description.ljust(16)} |{bar}| {pct:6.2f}%\n"
        return out

    def __str__(self) -> str:
        return self.__rich__()