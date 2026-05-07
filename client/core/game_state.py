"""
Client-side game state model.

This file stores the latest public game state received from the server.
The PyGame UI reads this object instead of reading sockets directly.
"""

import copy
import threading
from shared.constants import GRID_WIDTH, GRID_HEIGHT


class GameState:
    """Thread-safe client-side copy of the server public game state."""

    def __init__(self):
        """Initialize the local game state with default empty values."""
        self._lock = threading.Lock()

        self.player_id = None
        self.last_message = "Waiting for server..."
        self.last_packet_type = None
        self.connected = True
        self.board = ""

        self.state = {
            "grid_size": [GRID_WIDTH, GRID_HEIGHT],
            "players": {},
            "flowers": [],
            "garden_spots": [],
            "obstacles": [],
            "time_limit_seconds": None,
            "time_remaining_seconds": None,
            "winner": None,
            "recent_events": [],
        }

    def update_from_packet(self, packet):
        """Update the local state using a packet received from the server."""
        with self._lock:
            self.connected = True
            self.last_packet_type = packet.get("type", self.last_packet_type)

            if packet.get("player_id"):
                self.player_id = packet["player_id"]

            if packet.get("message"):
                self.last_message = packet["message"]

            if packet.get("board"):
                self.board = packet["board"]

            if packet.get("state"):
                self.state = packet["state"]

    def mark_connection_lost(self, message="Connection lost."):
        """Mark the client as disconnected and store the disconnect message."""
        with self._lock:
            self.connected = False
            self.last_message = message
            self.last_packet_type = "connection_lost"

    def snapshot(self):
        """Return a thread-safe copy of the current state for the UI."""
        with self._lock:
            return {
                "player_id": self.player_id,
                "last_message": self.last_message,
                "last_packet_type": self.last_packet_type,
                "connected": self.connected,
                "board": self.board,
                "state": copy.deepcopy(self.state),
            }