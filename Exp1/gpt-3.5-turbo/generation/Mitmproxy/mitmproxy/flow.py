class Flow:
    def __init__(self):
        self.id = None
        self.error = None
        self.metadata = {}

    def set_error(self, error: Exception):
        self.error = error

    def clear_error(self):
        self.error = None