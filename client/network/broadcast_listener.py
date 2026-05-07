"""
Client-side broadcast message listener thread.

This version supports both:
- Terminal UI: prints server messages
- PyGame UI: updates GameState silently
"""

import threading

from shared.message_types import WELCOME, COMMAND_RESULT, BROADCAST_STATE, BYE, ERROR
from shared.protocol import receive_packet


class BroadcastListener(threading.Thread):
    """Daemon thread listening for server broadcast messages."""

    def __init__(self, connection, game_state=None, print_messages=True):
        """Initialize the broadcast listener thread."""
        super().__init__(daemon=True)
        self.connection = connection
        self.game_state = game_state
        self.print_messages = print_messages
        self.running = True

    def run(self):
        """Continuously receive and process packets from the server."""
        while self.running:
            try:
                packet = receive_packet(self.connection)

                if self.game_state is not None:
                    self.game_state.update_from_packet(packet)

                if self.print_messages:
                    self._print_packet(packet)

                if packet.get("type") == BYE:
                    self.running = False
                    break

            except Exception as exc:
                if self.game_state is not None:
                    self.game_state.mark_connection_lost(
                        f"Broadcast listener stopped: {exc}"
                    )

                if self.print_messages:
                    print("Broadcast listener stopped:", exc)

                break

    def stop(self):
        """Stop the listener loop."""
        self.running = False

    def _print_packet(self, packet):
        """Display packet information in the terminal interface."""
        msg_type = packet.get("type")

        print("\n=== Broadcast message ===")

        if msg_type == WELCOME:
            print(packet.get("message"))
            print("Assigned player id:", packet.get("player_id"))

            if packet.get("board"):
                print(packet["board"])

        elif msg_type == COMMAND_RESULT:
            print(packet.get("message"))

            if packet.get("board"):
                print(packet["board"])

            state = packet.get("state", {})
            print("Time remaining:", state.get("time_remaining_seconds"))
            print("Winner:", state.get("winner"))

        elif msg_type == BROADCAST_STATE:
            if packet.get("board"):
                print(packet["board"])

            state = packet.get("state", {})
            print("Time remaining:", state.get("time_remaining_seconds"))
            print("Winner:", state.get("winner"))

            events = state.get("recent_events", [])

            if events:
                print("Recent events:")

                for event in events[-3:]:
                    print(f"  t={event['timestamp']}: {event['message']}")

        elif msg_type == BYE:
            print(packet.get("message"))

        elif msg_type == ERROR:
            print("Error:", packet.get("message"))

        else:
            print("Unknown broadcast message:", packet)

        print("=========================\n")