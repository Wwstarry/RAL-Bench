"""Task workflows"""

from typing import List, Tuple, Any
from .app.base import Task

class Signature:
    """Task signature"""
    
    def __init__(self, task: Task, args: Tuple = None, kwargs: dict = None):
        self.task = task
        self.args = args or ()
        self.kwargs = kwargs or {}
    
    def delay(self, *args, **kwargs):
        """Shortcut to apply_async"""
        return self.apply_async(args, kwargs)
    
    def apply_async(self, args: Tuple = None, kwargs: dict = None, **options):
        """Execute signature asynchronously"""
        final_args = self.args + (args or ())
        final_kwargs = self.kwargs.copy()
        final_kwargs.update(kwargs or {})
        return self.task.apply_async(final_args, final_kwargs, **options)

class group:
    """Group of tasks"""
    
    def __init__(self, tasks: List[Signature]):
        self.tasks = tasks
    
    def delay(self, *args, **kwargs):
        """Execute group"""
        return self.apply_async(args, kwargs)
    
    def apply_async(self, args: Tuple = None, kwargs: dict = None, **options):
        """Execute group asynchronously"""
        results = []
        for task in self.tasks:
            results.append(task.apply_async(args, kwargs, **options))
        return results

class chain:
    """Chain of tasks"""
    
    def __init__(self, *tasks: Signature):
        self.tasks = tasks
    
    def delay(self, *args, **kwargs):
        """Execute chain"""
        return self.apply_async(args, kwargs)
    
    def apply_async(self, args: Tuple = None, kwargs: dict = None, **options):
        """Execute chain asynchronously"""
        if not self.tasks:
            return None
        
        result = self.tasks[0].apply_async(args, kwargs, **options)
        for task in self.tasks[1:]:
            result = task.apply_async((result.get(),), kwargs, **options)
        
        return result