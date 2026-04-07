import json
import threading
import time


class BroadcastThread(threading.Thread):
    def __init__(self, client_list, data, interval=2):
        super().__init__()
        self.client_list = client_list
        self.data = data
        self.interval = interval

    def run(self):
        while True:
            payload = {
                'state': self.data.get_public_state(),
                'board': self.data.render_board(),
            }
            for addr, conn in self.client_list.get_clients().items():
                try:
                    self.send_data(conn, payload)
                except OSError:
                    self.client_list.remove_client(addr)
            time.sleep(self.interval)

    def send_data(self, conn, payload):
        message = json.dumps(payload, default=str)
        encoded = message.encode()
        length = len(encoded)
        conn.sendall(length.to_bytes(4, byteorder='big') + encoded)
