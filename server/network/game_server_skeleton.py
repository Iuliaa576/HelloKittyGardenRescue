"""
Server-side player connection handler (skeleton pattern).

Implements the server's half of the player-server communication protocol.
Each client gets one GameServerSkeleton instance running in a dedicated thread.

Connection Flow:
    1. Client connects with a command channel
    2. Client sends JOIN message with client_token
    3. This thread waits for the broadcast channel to be registered
    4. Once registered, sends WELCOME message
    5. Loops indefinitely receiving commands and forwarding results via broadcast

Command Processing:
    - MOVE: Move the player in a direction
    - PICK: Pick up a flower
    - PLANT: Plant a flower
    - STATE: Request game state (always succeeds, used for polling)
    - DISCONNECT: Gracefully disconnect

All responses are sent back to the client via the broadcast channel,
ensuring asymmetric communication where the server always initiates
to the client (push model).

Error Handling:
    - Catches exceptions during command processing
    - Always cleans up player and closes connections
    - Handles partial connection failures gracefully
"""

import threading

from shared.message_types import (
    JOIN,
    MOVE,
    PICK,
    PLANT,
    STATE,
    DISCONNECT,
    WELCOME,
    COMMAND_RESULT,
    BYE,
    ERROR,
)
from shared.protocol import receive_packet


class GameServerSkeleton(threading.Thread):
    """
    Handler for one client's command channel connection.
    
    Manages the join handshake, command processing loop, and graceful disconnect.
    """

    def __init__(self, connection, address, game_service, client_registry):
        """
        Initialize the server-side player handler.
        
        Args:
            connection: Socket connection for commands
            address (tuple): (host, port) of the client
            game_service (GameService): Game logic service
            client_registry (ClientRegistry): Broadcast connection registry
        """
        super().__init__(daemon=True)
        self.connection = connection
        self.address = address
        self.game_service = game_service
        self.client_registry = client_registry
        self.player_id = None                          # Assigned during join
        self.client_token = None                       # Client identifier

    def _send_to_broadcast_channel(self, payload):
        """
        Send a message to the client via their broadcast connection.
        
        Args:
            payload (dict): Message to send
        """
        if self.client_token:
            self.client_registry.send_to_client(self.client_token, payload)

    def run(self):
        """
        Main connection handler loop.
        
        Executes the join handshake, then processes commands indefinitely
        until disconnect or error.
        """
        try:
            # Receive and validate the first message (must be JOIN)
            first_message = receive_packet(self.connection)
            msg_type = first_message.get("type")

            if msg_type != JOIN:
                raise ValueError("First message must be a join request.")

            self.client_token = first_message.get("client_token")
            player_name = first_message.get("player_name", "Player")

            if not self.client_token:
                raise ValueError("Missing client_token in join request.")

            # Wait for broadcast channel to be registered
            # (client opens broadcast connection before command connection)
            ok = self.client_registry.wait_for_client(self.client_token, timeout=5.0)
            if not ok:
                raise ConnectionError("Broadcast channel was not registered in time.")

            # Register player in game
            self.player_id, player_info = self.game_service.join_player(player_name, self.address)

            # Send welcome message with initial state
            self._send_to_broadcast_channel({
                "type": WELCOME,
                "player_id": self.player_id,
                "message": f"Welcome {player_name} ({self.player_id})!",
                "player": player_info,
                "state": self.game_service.get_state(),
                "board": self.game_service.get_board(),
            })

            # Main command processing loop
            while True:
                request = receive_packet(self.connection)
                msg_type = request.get("type")

                if msg_type == MOVE:
                    # Process move command
                    direction = request.get("direction", "").lower()
                    print(f"[SERVER] Player {self.player_id} - MOVE {direction}")
                    ok, message = self.game_service.move(self.player_id, direction)

                elif msg_type == PICK:
                    # Process pick flower command
                    print(f"[SERVER] Player {self.player_id} - PICK")
                    ok, message = self.game_service.pick(self.player_id)

                elif msg_type == PLANT:
                    # Process plant flower command
                    print(f"[SERVER] Player {self.player_id} - PLANT")
                    ok, message = self.game_service.plant(self.player_id)

                elif msg_type == STATE:
                    # State request always succeeds (simple poll)
                    print(f"[SERVER] Player {self.player_id} - STATE")
                    ok, message = True, "State snapshot generated."

                elif msg_type == DISCONNECT:
                    # Graceful disconnect
                    print(f"[SERVER] Player {self.player_id} - DISCONNECT")
                    self._send_to_broadcast_channel({
                        "type": BYE,
                        "ok": True,
                        "message": f"{self.player_id} disconnected.",
                    })
                    return

                else:
                    # Unknown command
                    print(f"[SERVER] Player {self.player_id} - UNKNOWN: {msg_type}")
                    self._send_to_broadcast_channel({
                        "type": ERROR,
                        "ok": False,
                        "message": f"Unknown operation: {msg_type}",
                    })
                    continue

                # Send command result with updated game state
                self._send_to_broadcast_channel({
                    "type": COMMAND_RESULT,
                    "ok": ok,
                    "message": message,
                    "player_id": self.player_id,
                    "state": self.game_service.get_state(),
                    "board": self.game_service.get_board(),
                })

        except Exception as exc:
            print(self.address, "[SKELETON ERROR]:", exc)
        finally:
            # Always clean up: remove player and close connection
            if self.player_id:
                self.game_service.disconnect(self.player_id)
            self.connection.close()