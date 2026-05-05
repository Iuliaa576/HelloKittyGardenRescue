"""
Client-side game connection handler (stub pattern).

Manages both connection channels:
    1. Command channel: Sends player actions to the server
    2. Broadcast channel: Receives game state updates from the server

Connection Flow:
    1. Create GameClientStub with server address
    2. Call connect(player_name) to establish both channels
    3. Use move(), pick(), plant() to send commands
    4. Server responses arrive asynchronously on broadcast channel
    5. Call disconnect() for graceful shutdown

The stub handles:
    - Two-phase handshake (broadcast then command)
    - Token-based correlation between channels
    - Automatic broadcast listener thread startup
    - Safe connection cleanup on disconnect

Thread-Safety:
    The BroadcastListener runs as a daemon thread and receives messages
    independently, while the main thread sends commands via the command
    channel. Both connections are isolated and thread-safe.
"""

import socket
import time
import uuid

from shared.constants import DEFAULT_SERVER_ADDRESS, PORT, BROADCAST_PORT
from shared.message_types import JOIN, MOVE, PICK, PLANT, STATE, DISCONNECT
from shared.protocol import send_packet
from client.network.broadcast_listener import BroadcastListener


class GameClientStub:
    """Client-side connection handler for game communication."""

    def __init__(self, server_address=DEFAULT_SERVER_ADDRESS):
        """
        Initialize the game client stub.
        
        Args:
            server_address (str): Server IP/hostname (default: localhost)
        """
        self.server_address = server_address
        self.client_token = str(uuid.uuid4())              # Unique client identifier
        self.command_conn = None                           # Command channel
        self.broadcast_conn = None                         # Broadcast channel
        self.listener = None                               # Broadcast listener thread

    def connect(self, player_name):
        """
        Establish both broadcast and command channels with the server.
        
        Two-phase handshake:
        1. Connect to broadcast port and send client_token
        2. Start BroadcastListener thread
        3. Connect to command port and send JOIN message
        
        Args:
            player_name (str): Player's name for the game
        
        Raises:
            ConnectionError: If connection to server fails
        """
        # Phase 1: Connect to broadcast channel and register token
        self.broadcast_conn = socket.socket()
        self.broadcast_conn.connect((self.server_address, BROADCAST_PORT))
        send_packet(self.broadcast_conn, {"client_token": self.client_token})

        # Start listening for broadcast messages
        self.listener = BroadcastListener(self.broadcast_conn)
        self.listener.start()

        # Small delay to ensure broadcast connection is registered on server
        time.sleep(0.2)

        # Phase 2: Connect to command channel and send JOIN
        self.command_conn = socket.socket()
        self.command_conn.connect((self.server_address, PORT))
        send_packet(self.command_conn, {
            "type": JOIN,
            "client_token": self.client_token,
            "player_name": player_name,
        })

    def move(self, direction):
        """
        Send a move command to the server.
        
        Args:
            direction (str): 'up', 'down', 'left', or 'right'
        """
        send_packet(self.command_conn, {
            "type": MOVE,
            "direction": direction,
        })

    def pick(self):
        """Send a pick flower command to the server."""
        send_packet(self.command_conn, {"type": PICK})

    def plant(self):
        """Send a plant flower command to the server."""
        send_packet(self.command_conn, {"type": PLANT})

    def state(self):
        """Send a state request to the server."""
        send_packet(self.command_conn, {"type": STATE})

    def disconnect(self):
        """
        Gracefully disconnect from the game.
        
        Closes both command and broadcast channels.
        """
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