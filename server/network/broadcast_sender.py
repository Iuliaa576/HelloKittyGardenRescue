"""
Periodic game state broadcaster thread.

Runs continuously and periodically sends the current game state to all
connected clients via their broadcast channels.

This implements the "push" mechanism for game updates: rather than clients
polling for state changes, the server proactively sends the state at
regular intervals.

Handles network errors gracefully by removing clients with failed sends.
"""

import threading
import time

from shared.message_types import BROADCAST_STATE


class BroadcastSender(threading.Thread):
    """Daemon thread that broadcasts game state to all clients periodically."""

    def __init__(self, client_registry, game_service, interval=5):
        """
        Initialize the broadcast sender.
        
        Args:
            client_registry (ClientRegistry): Registry of broadcast connections
            game_service (GameService): Service layer for game state
            interval (int): Seconds between broadcasts (default: 5)
        """
        super().__init__(daemon=True)
        self.client_registry = client_registry
        self.game_service = game_service
        self.interval = interval

    def run(self):
        """
        Continuously broadcast game state at regular intervals.
        
        Sends a BROADCAST_STATE message with the current game state and
        board representation to all connected clients.
        
        Runs indefinitely, disconnecting clients that fail to receive.
        """
        while True:
            payload = {
                "type": BROADCAST_STATE,
                "state": self.game_service.get_state(),
                "board": self.game_service.get_board(),
            }

            for token, conn in self.client_registry.get_all_clients().items():
                try:
                    from shared.protocol import send_packet
                    send_packet(conn, payload)
                except OSError:
                    self.client_registry.remove_client(token)

            time.sleep(self.interval)