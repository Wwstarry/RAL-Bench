class Jail:
    def __init__(self, name):
        self.name = name
        self.filter = None
        self.actions = []
    
    def addFilter(self, filter_obj):
        self.filter = filter_obj
    
    def addAction(self, action_obj):
        self.actions.append(action_obj)

    def start(self):
        pass  # No daemon operations in safe mode

    def stop(self):
        pass