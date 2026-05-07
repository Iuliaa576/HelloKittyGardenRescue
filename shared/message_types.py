"""
Shared protocol message type constants.

This module defines all message types exchanged between clients and the
server during game communication.
"""

# CLIENT -> SERVER MESSAGES (Command Channel)

JOIN = "join"
MOVE = "move"
PICK = "pick"
PLANT = "plant"
STATE = "state"
DISCONNECT = "disconnect"

# SERVER -> CLIENT MESSAGES (Broadcast Channel)

WELCOME = "welcome"
COMMAND_RESULT = "command_result"
BROADCAST_STATE = "broadcast_state"
BYE = "bye"
ERROR = "error"
