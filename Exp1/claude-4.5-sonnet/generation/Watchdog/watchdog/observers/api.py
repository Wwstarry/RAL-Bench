"""
Core observer implementation.
"""

import os
import time
import threading
from pathlib import Path
from watchdog.events import (
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    DirCreatedEvent,
    DirModifiedEvent,
    DirDeletedEvent,
)


class Watch:
    """Represents a scheduled watch."""
    
    def __init__(self, path, handler, recursive):
        self.path = os.path.abspath(path)
        self.handler = handler
        self.recursive = recursive
        self.snapshot = {}
        self._update_snapshot()
    
    def _update_snapshot(self):
        """Update the snapshot of the watched directory."""
        new_snapshot = {}
        
        if not os.path.exists(self.path):
            self.snapshot = new_snapshot
            return
        
        if self.recursive:
            # Walk the entire tree
            for root, dirs, files in os.walk(self.path):
                # Add directories
                for d in dirs:
                    dir_path = os.path.join(root, d)
                    try:
                        stat = os.stat(dir_path)
                        new_snapshot[dir_path] = {
                            'is_dir': True,
                            'mtime': stat.st_mtime,
                            'size': stat.st_size,
                        }
                    except (OSError, FileNotFoundError):
                        pass
                
                # Add files
                for f in files:
                    file_path = os.path.join(root, f)
                    try:
                        stat = os.stat(file_path)
                        new_snapshot[file_path] = {
                            'is_dir': False,
                            'mtime': stat.st_mtime,
                            'size': stat.st_size,
                        }
                    except (OSError, FileNotFoundError):
                        pass
        else:
            # Only watch the immediate directory
            try:
                entries = os.listdir(self.path)
                for entry in entries:
                    entry_path = os.path.join(self.path, entry)
                    try:
                        stat = os.stat(entry_path)
                        is_dir = os.path.isdir(entry_path)
                        new_snapshot[entry_path] = {
                            'is_dir': is_dir,
                            'mtime': stat.st_mtime,
                            'size': stat.st_size,
                        }
                    except (OSError, FileNotFoundError):
                        pass
            except (OSError, FileNotFoundError):
                pass
        
        self.snapshot = new_snapshot
    
    def check_events(self):
        """Check for filesystem events and return them."""
        old_snapshot = self.snapshot.copy()
        self._update_snapshot()
        new_snapshot = self.snapshot
        
        events = []
        
        # Check for deleted files/directories
        for path in old_snapshot:
            if path not in new_snapshot:
                if old_snapshot[path]['is_dir']:
                    events.append(DirDeletedEvent(path))
                else:
                    events.append(FileDeletedEvent(path))
        
        # Check for created and modified files/directories
        for path in new_snapshot:
            if path not in old_snapshot:
                # Created
                if new_snapshot[path]['is_dir']:
                    events.append(DirCreatedEvent(path))
                else:
                    events.append(FileCreatedEvent(path))
            else:
                # Check for modification
                old_info = old_snapshot[path]
                new_info = new_snapshot[path]
                
                # Check if modified (mtime or size changed)
                if (new_info['mtime'] != old_info['mtime'] or 
                    new_info['size'] != old_info['size']):
                    if new_info['is_dir']:
                        events.append(DirModifiedEvent(path))
                    else:
                        events.append(FileModifiedEvent(path))
        
        return events


class Observer:
    """Filesystem observer that monitors directories for changes."""
    
    def __init__(self):
        self._watches = []
        self._thread = None
        self._stop_event = threading.Event()
        self._running = False
        self._lock = threading.Lock()
    
    def schedule(self, event_handler, path, recursive=False):
        """Schedule a watch on a path with an event handler.
        
        Args:
            event_handler: Handler to receive filesystem events
            path: Path to watch
            recursive: Whether to watch subdirectories
        
        Returns:
            Watch object
        """
        watch = Watch(path, event_handler, recursive)
        with self._lock:
            self._watches.append(watch)
        return watch
    
    def start(self):
        """Start the observer thread."""
        if self._running:
            return
        
        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the observer thread."""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
    
    def join(self, timeout=None):
        """Wait for the observer thread to finish."""
        if self._thread is not None:
            self._thread.join(timeout)
    
    def _run(self):
        """Main observer loop."""
        while not self._stop_event.is_set():
            with self._lock:
                watches = list(self._watches)
            
            for watch in watches:
                try:
                    events = watch.check_events()
                    for event in events:
                        try:
                            watch.handler.dispatch(event)
                        except Exception:
                            # Silently ignore handler exceptions
                            pass
                except Exception:
                    # Silently ignore watch exceptions
                    pass
            
            # Sleep for a short interval
            time.sleep(0.1)