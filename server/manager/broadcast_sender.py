import json
import threading
import time


class BroadcastThread(threading.Thread):
    def __init__(self, client_list, data, interval=10):
        super().__init__()
        self.client_list = client_list
        self.data = data
        self.interval = interval

    def run(self):
        while True:
            payload = {
                "type": "broadcast_state",
                "state": self.data.get_public_state(),
                "board": self.data.render_board(),
            }

            for token, conn in self.client_list.get_all_clients().items():
                try:
                    message = json.dumps(payload).encode()
                    conn.sendall(len(message).to_bytes(4, 'big') + message)
                except OSError:
                    self.client_list.remove_client(token)

            time.sleep(self.interval)