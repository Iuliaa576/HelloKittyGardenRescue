import socket
import threading

from data.data import DataStore
from server import PORT, BROADCAST_PORT
from server.manager.broadcast_sender import BroadcastThread
from server.manager.client_list import ClientList
from server.manager.process_client import ProcessClient


class Machine:
    def __init__(self):
        self.data_store = DataStore()
        self.broadcast_clients = ClientList()
        self.broadcast_thread = None

    def _accept_broadcast_clients(self):
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', BROADCAST_PORT))
        s.listen(5)
        print('Waiting for broadcast listeners on port:', BROADCAST_PORT)
        while True:
            conn, addr = s.accept()
            print('Broadcast client connected:', addr)
            self.broadcast_clients.add_client(addr, conn)

    def execute(self):
        broadcast_acceptor = threading.Thread(target=self._accept_broadcast_clients, daemon=True)
        broadcast_acceptor.start()

        self.broadcast_thread = BroadcastThread(self.broadcast_clients, self.data_store, interval=15)
        self.broadcast_thread.daemon = True
        self.broadcast_thread.start()

        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', PORT))
        s.listen(5)
        print('Garden Rescue server waiting on port:', PORT)
        while True:
            print('[SERVER] Waiting for a player...')
            connection, address = s.accept()
            print('[SERVER] Player connected:', address)
            process = ProcessClient(connection, address, self.data_store, self.broadcast_clients)
            process.start()
