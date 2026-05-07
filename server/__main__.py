"""
Server application entry point.

Starts the main game server responsible for handling player connections,
game state management, and broadcast communication.

Run:
    python -m server
"""

from server.manager.machine import Machine


if __name__ == "__main__":
    machine = Machine()
    machine.execute()