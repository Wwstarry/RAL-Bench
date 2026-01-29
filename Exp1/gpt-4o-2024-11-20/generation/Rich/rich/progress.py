# rich/progress.py

class Task:
    def __init__(self, description, total, completed=0):
        self.description = description
        self.total = total
        self.completed = completed

    def advance(self, steps=1):
        self.completed = min(self.completed + steps, self.total)

    def is_complete(self):
        return self.completed >= self.total

class Progress:
    def __init__(self):
        self.tasks = []

    def add_task(self, description, total):
        task = Task(description, total)
        self.tasks.append(task)
        return task

    def render(self):
        output = []
        for task in self.tasks:
            progress_bar = "[" + "#" * (task.completed * 10 // task.total) + "-" * (10 - task.completed * 10 // task.total) + "]"
            output.append(f"{task.description}: {progress_bar} {task.completed}/{task.total}")
        return "\n".join(output)