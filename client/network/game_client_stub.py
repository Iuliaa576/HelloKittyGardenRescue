"""
Client-side game connection handler.

Supports both:
- Terminal UI
- PyGame graphical UI
"""

import socket
import time
import uuid

from client.core.game_state import GameState
from client.network.broadcast_listener import BroadcastListener
from shared.constants import DEFAULT_SERVER_ADDRESS, PORT, BROADCAST_PORT
from shared.message_types import JOIN, MOVE, PICK, PLANT, STATE, DISCONNECT
from shared.protocol import send_packet


class GameClientStub:
    """Client-side stub for communicating with the game server."""

    def __init__(
        self,
        server_address=DEFAULT_SERVER_ADDRESS,
        game_state=None,
        print_broadcast=True,
    ):
        """Initialize the client stub and communication resources."""
        self.server_address = server_address
        self.client_token = str(uuid.uuid4())

        self.command_conn = None
        self.broadcast_conn = None
        self.listener = None

        # Shared state used by the graphical interface
        self.game_state = game_state or GameState()

        # Enable or disable terminal broadcast printing
        self.print_broadcast = print_broadcast

    def connect(self, player_name, character="hello_kitty"):
        """
        Connect to the server and initialize both communication channels.

        A broadcast channel is used for receiving updates,
        while a command channel is used for player actions.
        """

        # Connect broadcast channel
        self.broadcast_conn = socket.socket()
        self.broadcast_conn.connect((self.server_address, BROADCAST_PORT))

        send_packet(
            self.broadcast_conn,
            {
                "client_token": self.client_token
            }
        )

        # Start background listener thread
        self.listener = BroadcastListener(
            self.broadcast_conn,
            game_state=self.game_state,
            print_messages=self.print_broadcast,
        )
        self.listener.start()

        # Allow server time to register broadcast connection
        time.sleep(0.2)

        # Connect command channel
        self.command_conn = socket.socket()
        self.command_conn.connect((self.server_address, PORT))

        send_packet(
            self.command_conn,
            {
                "type": JOIN,
                "client_token": self.client_token,
                "player_name": player_name,
                "character": character,
            }
        )

    def move(self, direction):
        """Send a movement command to the server."""
        self._send_command({
            "type": MOVE,
            "direction": direction,
        })

    def pick(self):
        """Send a flower pickup command to the server."""
        self._send_command({"type": PICK})

    def plant(self):
        """Send a flower planting command to the server."""
        self._send_command({"type": PLANT})

    def state(self):
        """Request the latest game state from the server."""
        self._send_command({"type": STATE})

    def disconnect(self):
        """Gracefully disconnect the client from the server."""

        if self.listener is not None:
            self.listener.stop()

        if self.command_conn is not None:
            try:
                send_packet(self.command_conn, {"type": DISCONNECT})
            except OSError:
                pass

            try:
                self.command_conn.close()
            except OSError:
                pass

            self.command_conn = None

        if self.broadcast_conn is not None:
            try:
                self.broadcast_conn.close()
            except OSError:
                pass

            self.broadcast_conn = None

        self.game_state.mark_connection_lost("Disconnected from server.")

    def _send_command(self, payload):
        """Safely send a command packet to the server."""

        if self.command_conn is None:
            self.game_state.mark_connection_lost("Not connected to server.")
            return

        try:
            send_packet(self.command_conn, payload)
        except OSError as exc:
            self.game_state.mark_connection_lost(f"Command failed: {exc}")