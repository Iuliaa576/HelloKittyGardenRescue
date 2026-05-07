"""
Server package for Hello Kitty Garden Rescue.

This package contains the server-side components responsible for:
- Game state management
- Player synchronization
- Network communication
- Broadcast updates
- Concurrent client handling

The server validates player actions and maintains the centralized shared
game state for all connected clients.

Entry point:
    python -m server
"""