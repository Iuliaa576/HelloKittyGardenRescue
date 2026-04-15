import socket
import threading
import json

from data.data import DataStore
from server import PORT, BROADCAST_PORT
from server.manager.broadcast_sender import BroadcastThread
from server.manager.client_list import ClientList
from server.manager.process_client import ProcessClient


class Machine:
    def __init__(self):
        self.data_store = DataStore()
        self.broadcast_clients = ClientList()

    def _receive_exact(self, conn, n_bytes):
        data = b''
        while len(data) < n_bytes:
            chunk = conn.recv(n_bytes - len(data))
            if not chunk:
                raise ConnectionError("Connection closed while receiving data.")
            data += chunk
        return data

    def _receive_packet(self, conn):
        raw_length = self._receive_exact(conn, 4)
        length = int.from_bytes(raw_length, 'big')
        raw_data = self._receive_exact(conn, length)
        return json.loads(raw_data.decode())

    def _accept_broadcast_clients(self):
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', BROADCAST_PORT))
        s.listen(5)

        print("[SERVER] Waiting for broadcast clients on port:", BROADCAST_PORT)

        while True:
            conn, addr = s.accept()
            print("[SERVER] Broadcast socket connected:", addr)

            try:
                data = self._receive_packet(conn)
                token = data.get("client_token")

                if not token:
                    print("[SERVER] Broadcast registration missing token.")
                    conn.close()
                    continue

                self.broadcast_clients.add_client(token, conn)
                print("[SERVER] Registered broadcast client token:", token)

            except Exception as exc:
                print("[SERVER] Failed broadcast registration:", exc)
                conn.close()

    def execute(self):
        threading.Thread(target=self._accept_broadcast_clients, daemon=True).start()

        broadcast_thread = BroadcastThread(self.broadcast_clients, self.data_store, interval=5)
        broadcast_thread.daemon = True
        broadcast_thread.start()

        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', PORT))
        s.listen(5)

        print("[SERVER] Main server started on port:", PORT)

        while True:
            print("[SERVER] Waiting for command connection...")
            conn, addr = s.accept()
            print("[SERVER] Command client connected:", addr)
            process = ProcessClient(conn, addr, self.data_store, self.broadcast_clients)
            process.start()