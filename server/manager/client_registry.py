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
    """Manages broadcast connections for all connected clients."""

    def __init__(self):
        """Initialize an empty client registry."""
        self.clients = {}                               # token → socket connection
        self.lock = threading.Lock()

    def add_client(self, token, connection):
        """
        Register a client's broadcast connection.
        
        Args:
            token (str): Unique client identifier (UUID)
            connection: Socket connection for broadcasting to this client
        """
        with self.lock:
            self.clients[token] = connection

    def remove_client(self, token):
        """
        Unregister a client and close their broadcast connection.
        
        Safely closes the socket even if it's already closed.
        
        Args:
            token (str): Unique client identifier
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
        Check if a client is registered.
        
        Args:
            token (str): Unique client identifier
        
        Returns:
            bool: True if the client's broadcast connection is registered
        """
        with self.lock:
            return token in self.clients

    def wait_for_client(self, token, timeout=5.0):
        """
        Block until a client registers their broadcast connection.
        
        Used during the join handshake: the command channel (from
        GameServerSkeleton) waits for the broadcast channel to be
        registered before proceeding.
        
        Args:
            token (str): Unique client identifier to wait for
            timeout (float): Maximum time to wait in seconds
        
        Returns:
            bool: True if client registered within timeout, False otherwise
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
        
        Args:
            token (str): Unique client identifier
        
        Returns:
            socket or None: The client's broadcast connection, or None if not registered
        """
        with self.lock:
            return self.clients.get(token)

    def get_all_clients(self):
        """
        Get all registered client connections (for broadcast).
        
        Returns a snapshot of the client dictionary to avoid holding
        the lock during iteration.
        
        Returns:
            dict: Mapping of token → socket connection for all clients
        """
        with self.lock:
            return dict(self.clients)

    def send_to_client(self, token, payload):
        """
        Send a message to a specific client via their broadcast connection.
        
        Handles network errors gracefully by removing the client if
        sending fails.
        
        Args:
            token (str): Unique client identifier
            payload (dict): Message to send
        
        Returns:
            bool: True if message was sent successfully, False otherwise
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