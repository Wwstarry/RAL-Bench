import os

class FileSystemEvent:
    def __init__(self, src_path):
        self.src_path = os.path.abspath(src_path)
        self.event_type = None
        self.is_directory = os.path.isdir(self.src_path)

    def __repr__(self):
        return f"<{self.__class__.__name__}: src_path={self.src_path}>"

class FileCreatedEvent(FileSystemEvent):
    def __init__(self, src_path):
        super().__init__(src_path)
        self.event_type = "created"

class FileModifiedEvent(FileSystemEvent):
    def __init__(self, src_path):
        super().__init__(src_path)
        self.event_type = "modified"

class FileDeletedEvent(FileSystemEvent):
    def __init__(self, src_path):
        super().__init__(src_path)
        self.event_type = "deleted"

class FileSystemEventHandler:
    def on_any_event(self, event):
        pass

    def on_created(self, event):
        pass

    def on_modified(self, event):
        pass

    def on_deleted(self, event):
        pass

    def dispatch(self, event):
        self.on_any_event(event)
        if event.event_type == "created":
            self.on_created(event)
        elif event.event_type == "modified":
            self.on_modified(event)
        elif event.event_type == "deleted":
            self.on_deleted(event)