import uuid

class Flow:
    """
    A minimal, safe-to-evaluate placeholder for the base Flow class.
    Represents a single network transaction.
    """
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.client_conn = None
        self.server_conn = None
        self.error = None
        self.live = True
        self.intercepted = False

    def copy(self):
        """Creates a shallow copy of the flow."""
        # This is a very simplified copy for API compatibility.
        new_flow = self.__class__()
        new_flow.__dict__.update(self.__dict__)
        return new_flow

    def kill(self):
        """Marks the flow as killed."""
        self.live = False

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.id}>"