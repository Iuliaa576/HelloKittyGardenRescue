"""
Hello Kitty Garden Rescue - Server Application Entry Point

This module initializes and launches the game server.
The server manages all game state, handles client connections,
and orchestrates the multiplayer cooperative game.

Architecture:
    - Accepts multiple client connections simultaneously
    - Maintains centralized game state (DataStore)
    - Broadcasts periodic game updates to all players
    - Enforces game rules and validates player actions
    - Uses async communication with separate command and broadcast channels

Usage:
    python -m server

The server will listen on:
    - PORT 37000: Command channel (client actions)
    - PORT 37001: Broadcast channel (server → client updates)

It will accept connections from clients and manage up to 4 concurrent players.
"""

from server.manager.machine import Machine

if __name__ == "__main__":
    machine = Machine()
    machine.execute()