import threading
import json
import time


class ClientList:
    def __init__(self):
        self.clients = {}  # client_token -> connection
        self.lock = threading.Lock()

    def add_client(self, token, connection):
        with self.lock:
            self.clients[token] = connection

    def remove_client(self, token):
        with self.lock:
            conn = self.clients.pop(token, None)
            if conn:
                try:
                    conn.close()
                except OSError:
                    pass

    def has_client(self, token):
        with self.lock:
            return token in self.clients

    def wait_for_client(self, token, timeout=5.0):
        start = time.time()
        while time.time() - start < timeout:
            if self.has_client(token):
                return True
            time.sleep(0.05)
        return False

    def get_client_connection(self, token):
        with self.lock:
            return self.clients.get(token)

    def get_all_clients(self):
        with self.lock:
            return dict(self.clients)

    def send_to_client(self, token, payload):
        conn = self.get_client_connection(token)
        if not conn:
            return False

        try:
            message = json.dumps(payload).encode()
            conn.sendall(len(message).to_bytes(4, 'big') + message)
            return True
        except OSError:
            self.remove_client(token)
            return False