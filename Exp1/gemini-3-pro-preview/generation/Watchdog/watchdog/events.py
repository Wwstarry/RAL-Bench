class FileSystemEvent:
    def __init__(self, src_path):
        self.src_path = src_path
        self.event_type = None
        self.is_directory = False

    def __repr__(self):
        return "<%s: src_path=%r>" % (type(self).__name__, self.src_path)

class FileCreatedEvent(FileSystemEvent):
    def __init__(self, src_path):
        super().__init__(src_path)
        self.event_type = 'created'
        self.is_directory = False

class FileDeletedEvent(FileSystemEvent):
    def __init__(self, src_path):
        super().__init__(src_path)
        self.event_type = 'deleted'
        self.is_directory = False

class FileModifiedEvent(FileSystemEvent):
    def __init__(self, src_path):
        super().__init__(src_path)
        self.event_type = 'modified'
        self.is_directory = False

class DirCreatedEvent(FileSystemEvent):
    def __init__(self, src_path):
        super().__init__(src_path)
        self.event_type = 'created'
        self.is_directory = True

class DirDeletedEvent(FileSystemEvent):
    def __init__(self, src_path):
        super().__init__(src_path)
        self.event_type = 'deleted'
        self.is_directory = True

class DirModifiedEvent(FileSystemEvent):
    def __init__(self, src_path):
        super().__init__(src_path)
        self.event_type = 'modified'
        self.is_directory = True

class FileSystemEventHandler:
    def dispatch(self, event):
        self.on_any_event(event)
        method_map = {
            'created': self.on_created,
            'deleted': self.on_deleted,
            'modified': self.on_modified,
            'moved': self.on_moved,
        }
        method = method_map.get(event.event_type)
        if method:
            method(event)

    def on_any_event(self, event):
        pass

    def on_created(self, event):
        pass

    def on_deleted(self, event):
        pass

    def on_modified(self, event):
        pass

    def on_moved(self, event):
        pass