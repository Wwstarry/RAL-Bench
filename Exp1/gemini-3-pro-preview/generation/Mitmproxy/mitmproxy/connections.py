class ClientConnection:
    def __init__(self):
        self.id = "client-conn-id"
        self.address = ("127.0.0.1", 50000)
        self.timestamp_start = 0.0
        self.timestamp_end = None
        self.tls_established = False

class ServerConnection:
    def __init__(self):
        self.id = "server-conn-id"
        self.address = ("example.com", 80)
        self.timestamp_start = None
        self.timestamp_tcp_setup = None
        self.timestamp_tls_setup = None
        self.timestamp_end = None
        self.tls_established = False