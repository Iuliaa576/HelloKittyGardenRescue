import threading


class ClientList:
    def __init__(self):
        self.clients = {}
        self.lock = threading.Lock()

    def add_client(self, address, connection):
        with self.lock:
            self.clients[address] = connection

    def remove_client(self, address):
        with self.lock:
            conn = self.clients.pop(address, None)
            if conn:
                try:
                    conn.close()
                except OSError:
                    pass

    def get_clients(self):
        with self.lock:
            return dict(self.clients)
