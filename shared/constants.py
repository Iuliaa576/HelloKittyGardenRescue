"""
Shared game and network configuration constants.

This module contains:
- Network configuration values
- Game board dimensions
- Object spawn locations
- Gameplay settings
- Player and timer limits
"""

# NETWORK CONFIGURATION

SERVER_HOST = "0.0.0.0"
DEFAULT_SERVER_ADDRESS = "127.0.0.1"

PORT = 37000
BROADCAST_PORT = 37001

PACKET_LENGTH_SIZE = 4


# GAME BOARD CONFIGURATION

GRID_WIDTH = 10
GRID_HEIGHT = 10

# Flower spawn locations
FLOWERS = [
    (1, 1),
    (3, 2),
    (5, 1),
    (7, 3),
    (2, 6),
    (8, 2),
    (6, 7),
]

# Garden spots where flowers must be planted
GARDEN_SPOTS = {
    (0, 9): False,
    (2, 9): False,
    (4, 9): False,
    (6, 9): False,
    (8, 9): False,
    (7, 9): False,
    (9, 9): False,
}

# Obstacle positions
OBSTACLES = [
    (4, 4),
    (5, 4),
    (4, 5),
    (5, 5),

    (2, 2),
    (7, 2),

    (2, 7),
    (7, 7),
]

# GAMEPLAY SETTINGS

MIN_PLAYERS_TO_START = 2
MAX_PLAYERS = 4
TIME_LIMIT_SECONDS = 100
