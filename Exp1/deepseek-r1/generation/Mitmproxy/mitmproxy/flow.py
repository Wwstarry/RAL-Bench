class Flow:
    def __init__(self):
        self.id = None
        self.client_conn = None
        self.server_conn = None
        self.error = None
        self.intercepted = False
        self.marked = False
        self.mode = None
        self.metadata = {}