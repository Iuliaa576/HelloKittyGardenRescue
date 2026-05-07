"""
Periodic game state broadcaster thread.

This module periodically sends the current game state to all connected
clients through their broadcast connections.
"""

import threading
import time

from shared.message_types import BROADCAST_STATE


class BroadcastSender(threading.Thread):

    def __init__(self, client_registry, game_service, interval=5):
        """
        Initialize the periodic broadcast sender.
        """
        super().__init__(daemon=True)
        self.client_registry = client_registry
        self.game_service = game_service
        self.interval = interval

    def run(self):
        """
        Continuously send game state updates to all connected clients.
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