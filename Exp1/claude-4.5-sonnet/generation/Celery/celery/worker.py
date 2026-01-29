"""
Worker implementation
"""

import threading
import time
from typing import Optional


class Worker:
    """Celery worker"""
    
    def __init__(self, app, **kwargs):
        self.app = app
        self._running = False
        self._stop_event = threading.Event()
    
    def run(self):
        """Run the worker"""
        self._running = True
        
        while not self._stop_event.is_set():
            try:
                message = self.app.broker.consume(timeout=0.1)
                if message:
                    self._process_message(message)
            except Exception as exc:
                # Log error but continue
                print(f"Worker error: {exc}")
        
        self._running = False
    
    def _process_message(self, message):
        """Process a task message"""
        task_id = message['id']
        task_name = message['task']
        args = message.get('args', ())
        kwargs = message.get('kwargs', {})
        
        # Get task
        task = self.app._tasks.get(task_name)
        if task is None:
            self.app.backend.store_result(
                task_id,
                Exception(f'Task {task_name} not registered'),
                'FAILURE'
            )
            return
        
        # Execute task
        try:
            if self.app.conf.task_track_started:
                self.app.backend.store_result(task_id, None, 'STARTED')
            
            result = task(*args, **kwargs)
            self.app.backend.store_result(task_id, result, 'SUCCESS')
        except Exception as exc:
            self.app.backend.store_result(task_id, exc, 'FAILURE')
    
    def stop(self):
        """Stop the worker"""
        self._stop_event.set()
    
    def start(self):
        """Start the worker in a new thread"""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread