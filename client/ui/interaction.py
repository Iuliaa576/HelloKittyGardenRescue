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
        """Display available commands to the player."""
        print("Commands:")
        print("  move up|down|left|right")
        print("  pick")
        print("  plant")
        print("  state")
        print("  stop")
        print("  help")

    def execute(self):
        """
        Run the interactive client session.
        
        Prompts for server address and player name, establishes connection,
        displays help, then enters command loop.
        
        Command loop continues until:
        - Player issues 'stop' command, or
        - Network/connection error occurs, or
        - Server disconnects
        
        Ensures graceful cleanup in all cases.
        """
        # Get server address from user (with default)
        server_address = input(
            f"Server address [{DEFAULT_SERVER_ADDRESS}]: "
        ).strip() or DEFAULT_SERVER_ADDRESS

        # Get player name from user
        player_name = input("Player name: ").strip() or "Player"

        # Create and connect client
        client = GameClientStub(server_address=server_address)
        client.connect(player_name)

        # Display command help
        self._print_help()

        try:
            while True:
                cmd = input("Command: ").strip().lower()
                if not cmd:
                    continue

                parts = cmd.split()

                if parts[0] == "help":
                    # Display help message
                    self._print_help()

                elif parts[0] == "move" and len(parts) == 2:
                    # Move in specified direction
                    client.move(parts[1])

                elif parts[0] == "pick":
                    # Pick flower
                    client.pick()

                elif parts[0] == "plant":
                    # Plant flower
                    client.plant()

                elif parts[0] == "state":
                    # Request state snapshot
                    client.state()

                elif parts[0] == "stop":
                    # Gracefully disconnect and exit
                    return

                else:
                    # Invalid command
                    print("Invalid command")
        finally:
            # Always disconnect on exit (even if exception occurs)
            client.disconnect()