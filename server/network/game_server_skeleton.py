"""
Server-side player connection handler.

This module processes client commands received through the command socket
and interacts with the game service layer.
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

    def __init__(self, connection, address, game_service, client_registry):
        """Initialize the client command handler thread."""
        super().__init__(daemon=True)
        self.connection = connection
        self.address = address
        self.game_service = game_service
        self.client_registry = client_registry
        self.player_id = None
        self.client_token = None

    def _send_to_broadcast_channel(self, payload):
        """Send a packet to the client's broadcast connection."""
        if self.client_token:
            self.client_registry.send_to_client(self.client_token, payload)

    def run(self):
        """Process client requests until the connection closes."""
        try:
            first_message = receive_packet(self.connection)
            msg_type = first_message.get("type")

            if msg_type != JOIN:
                raise ValueError("First message must be a join request.")

            self.client_token = first_message.get("client_token")
            player_name = first_message.get("player_name", "Player")
            character = first_message.get("character", "hello_kitty")

            if not self.client_token:
                raise ValueError("Missing client_token in join request.")

            ok = self.client_registry.wait_for_client(
                self.client_token,
                timeout=5.0,
            )

            if not ok:
                raise ConnectionError("Broadcast channel was not registered in time.")

            self.player_id, player_info = self.game_service.join_player(
                player_name,
                character,
                self.address,
            )

            self._send_to_broadcast_channel(
                {
                    "type": WELCOME,
                    "player_id": self.player_id,
                    "message": f"Welcome {player_name} ({self.player_id})!",
                    "player": player_info,
                    "state": self.game_service.get_state(),
                    "board": self.game_service.get_board(),
                }
            )

            while True:
                request = receive_packet(self.connection)
                msg_type = request.get("type")

                if msg_type == MOVE:
                    direction = request.get("direction", "").lower()
                    print(f"[SERVER] Player {self.player_id} - MOVE {direction}")
                    ok, message = self.game_service.move(self.player_id, direction)

                elif msg_type == PICK:
                    print(f"[SERVER] Player {self.player_id} - PICK")
                    ok, message = self.game_service.pick(self.player_id)

                elif msg_type == PLANT:
                    print(f"[SERVER] Player {self.player_id} - PLANT")
                    ok, message = self.game_service.plant(self.player_id)

                elif msg_type == STATE:
                    print(f"[SERVER] Player {self.player_id} - STATE")
                    ok, message = True, "State snapshot generated."

                elif msg_type == DISCONNECT:
                    print(f"[SERVER] Player {self.player_id} - DISCONNECT")
                    self._send_to_broadcast_channel(
                        {
                            "type": BYE,
                            "ok": True,
                            "message": f"{self.player_id} disconnected.",
                        }
                    )
                    return

                else:
                    print(f"[SERVER] Player {self.player_id} - UNKNOWN: {msg_type}")
                    self._send_to_broadcast_channel(
                        {
                            "type": ERROR,
                            "ok": False,
                            "message": f"Unknown operation: {msg_type}",
                        }
                    )
                    continue

                self._send_to_broadcast_channel(
                    {
                        "type": COMMAND_RESULT,
                        "ok": ok,
                        "message": message,
                        "player_id": self.player_id,
                        "state": self.game_service.get_state(),
                        "board": self.game_service.get_board(),
                    }
                )

        except Exception as exc:
            print(self.address, "[SKELETON ERROR]:", exc)

        finally:
            if self.player_id:
                self.game_service.disconnect(self.player_id)

            if self.client_token:
                self.client_registry.remove_client(self.client_token)

            try:
                self.connection.close()
            except OSError:
                pass