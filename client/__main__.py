"""
Client application entry point.

Starts the terminal-based interaction interface for the game client.

Run:
    python -m client
"""

from client.ui.interaction import Interaction


if __name__ == "__main__":
    interaction = Interaction()
    interaction.execute()