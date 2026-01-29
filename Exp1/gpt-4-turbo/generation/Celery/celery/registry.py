class TaskRegistry:
    def __init__(self):
        self._tasks = {}

    def register(self, task):
        self._tasks[task.name] = task

    def get(self, name):
        return self._tasks.get(name)