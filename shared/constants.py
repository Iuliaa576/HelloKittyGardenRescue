"""
Game configuration constants for Hello Kitty Garden Rescue.

This module defines all game parameters and network configuration settings,
allowing for easy modification and future support for difficulty levels.

Network Configuration:
    - SERVER_HOST: Address the server binds to
    - DEFAULT_SERVER_ADDRESS: Default address clients connect to
    - PORT: Command channel port (client → server)
    - BROADCAST_PORT: Broadcast channel port (server → clients)
    - PACKET_LENGTH_SIZE: Size of packet length prefix in bytes

Game Board:
    - GRID_WIDTH, GRID_HEIGHT: Board dimensions
    - FLOWERS: Initial flower spawn locations
    - GARDEN_SPOTS: Target garden spots to fill (position → occupied status)
    - OBSTACLES: Fixed obstacle positions

Game Rules:
    - MAX_PLAYERS: Maximum number of concurrent players
    - TIME_LIMIT_SECONDS: Game duration in seconds
"""

# ============================================================================
# NETWORK CONFIGURATION
# ============================================================================

SERVER_HOST = "0.0.0.0"                      # Server bind host (accept all interfaces)
DEFAULT_SERVER_ADDRESS = "127.0.0.1"         # Default server address for clients

PORT = 37000                                  # Main command channel port
BROADCAST_PORT = 37001                        # Broadcast update channel port

PACKET_LENGTH_SIZE = 4                        # Size of packet length prefix (bytes)

# ============================================================================
# GAME BOARD CONFIGURATION
# ============================================================================

GRID_WIDTH = 6                                # Board width in tiles
GRID_HEIGHT = 6                               # Board height in tiles

# Flower spawn locations (fixed positions on the board)
FLOWERS = [
    (0, 5),                                   # Flower at (x=0, y=5)
    (2, 2),                                   # Flower at (x=2, y=2)
    (5, 0),                                   # Flower at (x=5, y=0)
]

# Garden spots where flowers must be planted (position → occupied status)
# Key: (x, y) tuple representing position
# Value: False = empty, True = occupied with a planted flower
GARDEN_SPOTS = {
    (5, 5): False,                            # Garden spot at (x=5, y=5)
    (0, 0): False,                            # Garden spot at (x=0, y=0)
    (3, 4): False,                            # Garden spot at (x=3, y=4)
}

# Obstacle positions that block player movement
OBSTACLES = [
    (1, 1),                                   # Obstacle at (x=1, y=1)
    (1, 2),                                   # Obstacle at (x=1, y=2)
    (4, 2),                                   # Obstacle at (x=4, y=2)
    (4, 3),                                   # Obstacle at (x=4, y=3)
]

# ============================================================================
# GAME RULES CONFIGURATION
# ============================================================================

MAX_PLAYERS = 4                               # Maximum concurrent players allowed
TIME_LIMIT_SECONDS = 300                      # Game duration limit (5 minutes)
