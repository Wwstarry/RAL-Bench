import threading
import time
import os
from watchdog.observers.api import ObservedWatch
from watchdog.events import (
    FileCreatedEvent, FileDeletedEvent, FileModifiedEvent,
    DirCreatedEvent, DirDeletedEvent, DirModifiedEvent
)

class Observer(threading.Thread):
    def __init__(self, timeout=0.1):
        super().__init__()
        self._watches = []
        self._stop_event = threading.Event()
        self._timeout = timeout
        self.daemon = True

    def schedule(self, event_handler, path, recursive=False):
        watch = ObservedWatch(path, recursive)
        abs_path = os.path.abspath(path)
        snapshot = self._take_snapshot(abs_path, recursive)
        self._watches.append({
            'watch': watch,
            'handler': event_handler,
            'path': abs_path,
            'recursive': recursive,
            'snapshot': snapshot
        })
        return watch

    def unschedule(self, watch):
        self._watches = [w for w in self._watches if w['watch'] != watch]

    def unschedule_all(self):
        self._watches = []

    def run(self):
        while not self._stop_event.is_set():
            # Iterate over a copy to allow modification during iteration
            for w in list(self._watches):
                if w not in self._watches:
                    continue
                try:
                    new_snapshot = self._take_snapshot(w['path'], w['recursive'])
                    self._process_events(w, new_snapshot)
                    w['snapshot'] = new_snapshot
                except Exception:
                    pass
            time.sleep(self._timeout)

    def stop(self):
        self._stop_event.set()

    def _take_snapshot(self, path, recursive):
        snapshot = {}
        if not os.path.exists(path):
            return snapshot
        
        def add_item(p):
            try:
                st = os.stat(p)
                # Key by path, value is (mtime, is_dir)
                snapshot[p] = (st.st_mtime, os.path.isdir(p))
            except OSError:
                pass

        # Add the root path itself
        add_item(path)

        if os.path.isdir(path):
            if recursive:
                for root, dirs, files in os.walk(path):
                    for d in dirs:
                        add_item(os.path.join(root, d))
                    for f in files:
                        add_item(os.path.join(root, f))
            else:
                try:
                    for name in os.listdir(path):
                        add_item(os.path.join(path, name))
                except OSError:
                    pass
        return snapshot

    def _process_events(self, watch_ctx, new_snapshot):
        old_snapshot = watch_ctx['snapshot']
        handler = watch_ctx['handler']
        
        old_paths = set(old_snapshot.keys())
        new_paths = set(new_snapshot.keys())
        
        # Deleted
        for p in old_paths - new_paths:
            mtime, is_dir = old_snapshot[p]
            if is_dir:
                handler.dispatch(DirDeletedEvent(p))
            else:
                handler.dispatch(FileDeletedEvent(p))

        # Created
        for p in new_paths - old_paths:
            mtime, is_dir = new_snapshot[p]
            if is_dir:
                handler.dispatch(DirCreatedEvent(p))
            else:
                handler.dispatch(FileCreatedEvent(p))
                
        # Modified
        for p in old_paths & new_paths:
            old_mtime, old_is_dir = old_snapshot[p]
            new_mtime, new_is_dir = new_snapshot[p]
            
            if new_mtime != old_mtime:
                if new_is_dir:
                    handler.dispatch(DirModifiedEvent(p))
                else:
                    handler.dispatch(FileModifiedEvent(p))