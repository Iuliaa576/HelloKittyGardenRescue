"""
Client registry for managing broadcast connections.

Maintains a mapping of client tokens to broadcast socket connections,
allowing the server to send targeted messages to specific clients.

Each client establishes two connections:
1. Command channel: For sending player actions to the server
2. Broadcast channel: For receiving game state updates and messages

This registry manages only the broadcast channels (connection #2).

Thread-Safety:
    All operations are protected by a lock to ensure consistency
    when multiple server threads access the registry simultaneously.
"""

import threading
import time

from shared.protocol import send_packet


class ClientRegistry:
    def __init__(self):
        """Initialize the client registry."""
        self.clients = {}                               # token → socket connection
        self.lock = threading.Lock()

    def add_client(self, token, connection):
        """
        Register a client's broadcast connection.
        """
        with self.lock:
            self.clients[token] = connection

    def remove_client(self, token):
        """
        Unregister a client and close their broadcast connection.
        Safely closes the socket even if it's already closed.
        """
        with self.lock:
            conn = self.clients.pop(token, None)
            if conn:
                try:
                    conn.close()
                except OSError:
                    pass

    def has_client(self, token):
        """
        Check whether a client token is registered.
        """
        with self.lock:
            return token in self.clients

    def wait_for_client(self, token, timeout=5.0):
        """
        Block until a client registers their broadcast connection.
        Used during the join handshake: the command channel (from
        GameServerSkeleton) waits for the broadcast channel to be
        registered before proceeding.
        """
        start = time.time()
        while time.time() - start < timeout:
            if self.has_client(token):
                return True
            time.sleep(0.05)
        return False

    def get_client(self, token):
        """
        Get a client's broadcast connection.
        """
        with self.lock:
            return self.clients.get(token)

    def get_all_clients(self):
        """
        Return a snapshot of all registered broadcast clients.
        """
        with self.lock:
            return dict(self.clients)

    def send_to_client(self, token, payload):
        """
        Send a packet to a specific broadcast client.
        """
        conn = self.get_client(token)
        if not conn:
            return False
        try:
            send_packet(conn, payload)
            return True
        except OSError:
            self.remove_client(token)
            return False