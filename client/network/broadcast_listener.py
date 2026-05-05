"""
Client-side broadcast message listener thread.

Runs as a daemon thread and continuously listens for messages from the server
via the broadcast channel. Processes and displays messages to the player.

Message Types Handled:
    - WELCOME: Initial join confirmation with game state
    - COMMAND_RESULT: Response to a player action with updated state
    - BROADCAST_STATE: Periodic game state update
    - BYE: Disconnect notification

The listener runs independently and terminates only when the connection
closes (either due to network error or server shutdown).
"""

import threading

from shared.message_types import WELCOME, COMMAND_RESULT, BROADCAST_STATE, BYE


class BroadcastListener(threading.Thread):
    """Daemon thread listening for server broadcast messages."""

    def __init__(self, connection):
        """
        Initialize the broadcast listener.
        
        Args:
            connection: Socket connection to receive broadcast messages from
        """
        super().__init__(daemon=True)
        self.connection = connection

    def run(self):
        """
        Continuously receive and display broadcast messages.
        
        Processes different message types and displays relevant information
        to the player (messages, board state, time remaining, etc.).
        
        Runs until the broadcast connection closes.
        """
        from shared.protocol import receive_packet

        while True:
            try:
                data = receive_packet(self.connection)
                msg_type = data.get("type")

                print("\n=== Broadcast message ===")

                if msg_type == WELCOME:
                    # Display welcome message with initial state
                    print(data.get("message"))
                    print("Assigned player id:", data.get("player_id"))
                    if data.get("board"):
                        print(data["board"])

                elif msg_type == COMMAND_RESULT:
                    # Display command result message and updated state
                    print(data.get("message"))
                    if data.get("board"):
                        print(data["board"])

                    state = data.get("state", {})
                    print("Time remaining:", state.get("time_remaining_seconds"))
                    print("Winner:", state.get("winner"))

                elif msg_type == BROADCAST_STATE:
                    # Display periodic state broadcast (board, time, recent events)
                    if data.get("board"):
                        print(data["board"])

                    state = data.get("state", {})
                    print("Time remaining:", state.get("time_remaining_seconds"))
                    print("Winner:", state.get("winner"))

                    # Show last 3 recent events
                    events = state.get("recent_events", [])
                    if events:
                        print("Recent events:")
                        for event in events[-3:]:
                            print(f"  t={event['timestamp']}: {event['message']}")

                elif msg_type == BYE:
                    # Display disconnect message
                    print(data.get("message"))

                else:
                    # Unknown message type
                    print("Unknown broadcast message:", data)

                print("=========================\n")

            except Exception as exc:
                print("Broadcast listener stopped:", exc)
                break