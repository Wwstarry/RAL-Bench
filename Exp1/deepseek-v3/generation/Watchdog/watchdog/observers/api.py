"""
Observer API for monitoring file systems.
"""

import os
import time
import threading
from collections import defaultdict
from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileDeletedEvent


class BaseObserver:
    """Base observer class."""
    
    def __init__(self):
        self._handlers = []
        self._lock = threading.RLock()
        self._should_stop = False
        self._thread = None
    
    def schedule(self, event_handler, path, recursive=False):
        """Schedule watching a path with the given event handler."""
        with self._lock:
            if not os.path.exists(path):
                raise OSError(f"Path does not exist: {path}")
            
            self._handlers.append({
                'handler': event_handler,
                'path': os.path.abspath(path),
                'recursive': recursive,
                'snapshot': self._take_snapshot(path, recursive)
            })
    
    def _take_snapshot(self, path, recursive):
        """Take a snapshot of the current file system state."""
        snapshot = {}
        
        if os.path.isfile(path):
            snapshot[path] = os.path.getmtime(path)
            return snapshot
        
        for root, dirs, files in os.walk(path):
            for name in files + dirs:
                full_path = os.path.join(root, name)
                snapshot[full_path] = os.path.getmtime(full_path)
            
            if not recursive:
                break
        
        return snapshot
    
    def _detect_changes(self, old_snapshot, new_snapshot):
        """Detect changes between two snapshots."""
        events = []
        
        # Check for created and modified files
        for path, new_mtime in new_snapshot.items():
            if path not in old_snapshot:
                events.append(FileCreatedEvent(path))
            elif new_mtime != old_snapshot[path]:
                events.append(FileModifiedEvent(path))
        
        # Check for deleted files
        for path in old_snapshot:
            if path not in new_snapshot:
                events.append(FileDeletedEvent(path))
        
        return events
    
    def start(self):
        """Start the observer."""
        if self._thread and self._thread.is_alive():
            return
        
        self._should_stop = False
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()
    
    def stop(self):
        """Stop the observer."""
        self._should_stop = True
        if self._thread:
            self._thread.join(timeout=5)
    
    def join(self):
        """Wait for the observer thread to complete."""
        if self._thread:
            self._thread.join()
    
    def _run(self):
        """Main observer loop."""
        while not self._should_stop:
            with self._lock:
                for handler_info in self._handlers:
                    new_snapshot = self._take_snapshot(
                        handler_info['path'], 
                        handler_info['recursive']
                    )
                    
                    events = self._detect_changes(
                        handler_info['snapshot'], 
                        new_snapshot
                    )
                    
                    for event in events:
                        handler_info['handler'].dispatch(event)
                    
                    # Update snapshot for next iteration
                    handler_info['snapshot'] = new_snapshot
            
            time.sleep(0.1)  # Polling interval


class Observer(BaseObserver):
    """
    Observer that monitors file system events.
    This is a polling-based implementation for maximum compatibility.
    """
    
    def __init__(self, timeout=1.0):
        super().__init__()
        self.timeout = timeout
    
    def _run(self):
        """Main observer loop with configurable timeout."""
        while not self._should_stop:
            with self._lock:
                for handler_info in self._handlers:
                    new_snapshot = self._take_snapshot(
                        handler_info['path'], 
                        handler_info['recursive']
                    )
                    
                    events = self._detect_changes(
                        handler_info['snapshot'], 
                        new_snapshot
                    )
                    
                    for event in events:
                        handler_info['handler'].dispatch(event)
                    
                    handler_info['snapshot'] = new_snapshot
            
            time.sleep(self.timeout)