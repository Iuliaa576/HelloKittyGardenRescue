"""
Message type constants for the distributed game protocol.

Defines all message types used in client-server communication across both
the command channel (client → server) and broadcast channel (server → clients).

Client → Server Messages (Command Channel):
    - JOIN: Initial join request with player info
    - MOVE: Player movement request (up/down/left/right)
    - PICK: Request to pick up a flower
    - PLANT: Request to plant a flower in a garden spot
    - STATE: Request for current game state snapshot
    - DISCONNECT: Graceful disconnect notification

Server → Client Messages (Broadcast Channel):
    - WELCOME: Welcome message sent when player joins
    - COMMAND_RESULT: Response to a player command with game state update
    - BROADCAST_STATE: Periodic game state broadcast to all clients
    - BYE: Disconnect notification when a player leaves
    - ERROR: Error response to invalid commands
"""

# ============================================================================
# CLIENT → SERVER MESSAGES (Command Channel)
# ============================================================================

JOIN = "join"                                 # Player join request (first message)
MOVE = "move"                                 # Move in a direction (up/down/left/right)
PICK = "pick"                                 # Pick up a flower from current tile
PLANT = "plant"                               # Plant a carried flower at current tile
STATE = "state"                               # Request current game state
DISCONNECT = "disconnect"                     # Graceful disconnect message

# ============================================================================
# SERVER → CLIENT MESSAGES (Broadcast Channel)
# ============================================================================

WELCOME = "welcome"                           # Welcome message with initial game state
COMMAND_RESULT = "command_result"             # Result of a player action with updated state
BROADCAST_STATE = "broadcast_state"           # Periodic state update broadcast to all clients
BYE = "bye"                                   # Disconnect confirmation or notification
ERROR = "error"                               # Error response to invalid operations
