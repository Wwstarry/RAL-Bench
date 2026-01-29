"""
Core observer API for filesystem monitoring.
"""

import os
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict

from watchdog.events import CreatedEvent, ModifiedEvent, DeletedEvent


class FileSystemEventHandler:
    """Base class for filesystem event handlers."""
    
    def on_created(self, event):
        """Called when a file or directory is created."""
        pass
    
    def on_modified(self, event):
        """Called when a file or directory is modified."""
        pass
    
    def on_deleted(self, event):
        """Called when a file or directory is deleted."""
        pass
    
    def on_moved(self, event):
        """Called when a file or directory is moved or renamed."""
        pass


class Observer:
    """
    Filesystem event observer that monitors directories for changes.
    """
    
    def __init__(self):
        """Initialize the observer."""
        self._handlers: List[tuple] = []
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._stop_event = threading.Event()
        self._file_mtimes: Dict[str, float] = {}
        self._file_sizes: Dict[str, int] = {}
        self._existing_files: Dict[str, Set[str]] = defaultdict(set)
    
    def schedule(self, handler: FileSystemEventHandler, path: str, recursive: bool = False) -> None:
        """
        Schedule a handler to monitor a path.
        
        Args:
            handler: FileSystemEventHandler instance.
            path: Path to monitor.
            recursive: Whether to monitor subdirectories.
        """
        self._handlers.append((handler, path, recursive))
    
    def start(self) -> None:
        """Start the observer."""
        if self._running:
            return
        
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the observer."""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
    
    def join(self) -> None:
        """Wait for the observer thread to finish."""
        if self._thread is not None:
            self._thread.join()
    
    def _run(self) -> None:
        """Main observer loop."""
        # Initialize file tracking for all monitored paths
        for handler, path, recursive in self._handlers:
            self._scan_directory(path, recursive)
        
        # Monitor for changes
        while self._running and not self._stop_event.is_set():
            for handler, path, recursive in self._handlers:
                self._check_directory(handler, path, recursive)
            
            time.sleep(0.1)
    
    def _scan_directory(self, path: str, recursive: bool) -> None:
        """Scan a directory and record initial state."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return
        
        if path_obj.is_file():
            self._record_file_state(path)
            return
        
        # Scan directory
        try:
            for entry in path_obj.iterdir():
                if entry.is_file():
                    self._record_file_state(str(entry))
                elif entry.is_dir() and recursive:
                    self._scan_directory(str(entry), recursive)
        except (OSError, PermissionError):
            pass
    
    def _record_file_state(self, file_path: str) -> None:
        """Record the current state of a file."""
        try:
            stat = os.stat(file_path)
            self._file_mtimes[file_path] = stat.st_mtime
            self._file_sizes[file_path] = stat.st_size
        except (OSError, FileNotFoundError):
            pass
    
    def _check_directory(self, handler: FileSystemEventHandler, path: str, recursive: bool) -> None:
        """Check a directory for changes."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return
        
        if path_obj.is_file():
            self._check_file(handler, path)
            return
        
        # Get current files in directory
        current_files: Set[str] = set()
        try:
            for entry in path_obj.iterdir():
                current_files.add(str(entry))
                
                if entry.is_file():
                    self._check_file(handler, str(entry))
                elif entry.is_dir() and recursive:
                    self._check_directory(handler, str(entry), recursive)
        except (OSError, PermissionError):
            pass
        
        # Check for deleted files
        previous_files = self._existing_files.get(path, set())
        for deleted_path in previous_files - current_files:
            if deleted_path not in self._file_mtimes:
                # File was already deleted, skip
                continue
            
            is_dir = not deleted_path.endswith(tuple([f for f in previous_files if os.path.isfile(f) if f == deleted_path]))
            event = DeletedEvent(deleted_path, is_directory=False)
            handler.on_deleted(event)
            
            # Clean up tracking
            self._file_mtimes.pop(deleted_path, None)
            self._file_sizes.pop(deleted_path, None)
        
        # Update existing files set
        self._existing_files[path] = current_files
    
    def _check_file(self, handler: FileSystemEventHandler, file_path: str) -> None:
        """Check a file for changes."""
        try:
            stat = os.stat(file_path)
            current_mtime = stat.st_mtime
            current_size = stat.st_size
            
            if file_path not in self._file_mtimes:
                # New file
                event = CreatedEvent(file_path, is_directory=False)
                handler.on_created(event)
                self._file_mtimes[file_path] = current_mtime
                self._file_sizes[file_path] = current_size
            else:
                # Check if modified
                previous_mtime = self._file_mtimes[file_path]
                previous_size = self._file_sizes.get(file_path, current_size)
                
                if current_mtime != previous_mtime or current_size != previous_size:
                    event = ModifiedEvent(file_path, is_directory=False)
                    handler.on_modified(event)
                    self._file_mtimes[file_path] = current_mtime
                    self._file_sizes[file_path] = current_size
        except (OSError, FileNotFoundError):
            # File was deleted
            if file_path in self._file_mtimes:
                event = DeletedEvent(file_path, is_directory=False)
                handler.on_deleted(event)
                self._file_mtimes.pop(file_path, None)
                self._file_sizes.pop(file_path, None)