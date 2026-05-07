"""
Client-side user interaction layer.

Handles the command-line interface for players to interact with the game.
Accepts server address and player name input, then presents a command loop
for issuing game commands.

Supported Commands:
    - move up|down|left|right : Move in the specified direction
    - pick : Pick up a flower from current tile
    - plant : Plant a flower at current tile
    - state : Request game state snapshot
    - help : Display command list
    - stop : Disconnect and exit

The interaction class manages the connection lifecycle and command dispatch
to the GameClientStub, ensuring graceful cleanup on exit.
"""

from client.network.game_client_stub import GameClientStub
from shared.constants import DEFAULT_SERVER_ADDRESS


class Interaction:
    """Command-line interface for game interaction."""

    def _print_help(self):
        """Display the list of supported commands."""
        print("Commands:")
        print("  move up|down|left|right")
        print("  pick")
        print("  plant")
        print("  state")
        print("  stop")
        print("  help")

    def execute(self):
        """
        Start the terminal-based game session.

        Prompts the player for connection information,
        establishes the connection to the server,
        then continuously processes player commands.
        """

        # Get server address from user
        server_address = input(
            f"Server address [{DEFAULT_SERVER_ADDRESS}]: "
        ).strip() or DEFAULT_SERVER_ADDRESS

        # Get player name
        player_name = input("Player name: ").strip() or "Player"

        # Create and connect client
        client = GameClientStub(server_address=server_address)
        client.connect(player_name)

        # Show available commands
        self._print_help()

        try:
            while True:
                cmd = input("Command: ").strip().lower()

                if not cmd:
                    continue

                parts = cmd.split()

                if parts[0] == "help":
                    self._print_help()

                elif parts[0] == "move" and len(parts) == 2:
                    client.move(parts[1])

                elif parts[0] == "pick":
                    client.pick()

                elif parts[0] == "plant":
                    client.plant()

                elif parts[0] == "state":
                    client.state()

                elif parts[0] == "stop":
                    return

                else:
                    print("Invalid command")

        finally:
            # Ensure client disconnects on exit
            client.disconnect()