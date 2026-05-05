# Hello Kitty Garden Rescue - Code Documentation

## Overview

This is a **distributed multiplayer game prototype** written in Python, implementing a client-server architecture with asymmetric communication channels.

**Game Objective**: Players cooperatively collect flowers and plant them in garden spots before time expires.

---

## Architecture Summary

### Communication Model

The system uses **asymmetric communication**:

- **Client → Server (Command Channel, Port 37000)**
  - Clients send player actions (move, pick, plant)
  - Uses request/response pattern at the connection level

- **Server → Client (Broadcast Channel, Port 37001)**
  - Server sends welcome messages, command results, periodic updates, and disconnects
  - Unidirectional push model
  - All responses delivered via broadcast

### Key Design Patterns

- **Skeleton Pattern** (`GameServerSkeleton`): Handles one client connection per thread
- **Stub Pattern** (`GameClientStub`): Client-side connection handler
- **Service Facade** (`GameService`): Abstraction layer for game operations
- **Data Access Object** (`DataStore`): Centralized state management
- **Registry Pattern** (`ClientRegistry`): Tracks active broadcast connections

---

## Game Logic

### Player Actions

#### Movement
- **Valid**: Within board bounds, not an obstacle, not occupied by another player
- **Result**: Updates player position and logs event

#### Pick Flower
- **Preconditions**: Player is on a flower tile, not already carrying a flower
- **Effect**: Removes flower from board, sets `player['has_flower'] = True`
- **Result**: Success or error message

#### Plant Flower
- **Preconditions**: Player has flower, on garden spot, garden spot not occupied
- **Effect**: Sets garden spot as occupied, player loses flower
- **Win Condition**: If all garden spots filled, game ends with "players" winning

### Game End Conditions

1. **Players Win**: All three garden spots filled with flowers
2. **Time Expires**: Time remaining reaches 0 (players lose)
3. **Game Finished**: No further actions allowed once winner is determined

---

## Threading Model

### Server

```
Main Thread (Command Listener)
├─ Accept connections → spawn GameServerSkeleton
└─ Each GameServerSkeleton runs in its own thread
    └─ Reads from command channel
    └─ Writes to broadcast channel (via ClientRegistry)

Broadcast Thread
├─ Accept connections → register in ClientRegistry
└─ Hold open connections

BroadcastSender Thread
└─ Every 5 seconds: send state to all registered clients

DataStore Lock
└─ Protects all state mutations (threads acquire when accessing game state)
```

### Client

```
Main Thread (User Input)
├─ Read commands from stdin
└─ Send via command_conn (GameClientStub)

BroadcastListener Thread (daemon)
├─ Listen on broadcast_conn
└─ Display messages to stdout
```

---

## Data Structures

### Player State (DataStore.players)
```python
{
    'position': (x, y),           # Current position
    'has_flower': bool,           # Carrying a flower?
    'connected': bool,            # Still connected?
    'address': 'host:port',       # Client address
    'name': 'player_name'         # Player's name
}
```

### Public Game State (from get_public_state())
```python
{
    'grid_size': [6, 6],
    'players': {
        'P1': {'position': [2, 3], 'has_flower': False, 'connected': True},
        ...
    },
    'flowers': [[0, 5], [2, 2], [5, 0]],
    'garden_spots': [
        {'position': [5, 5], 'occupied': False},
        {'position': [0, 0], 'occupied': True},
        {'position': [3, 4], 'occupied': False}
    ],
    'obstacles': [[1, 1], [1, 2], [4, 2], [4, 3]],
    'time_limit_seconds': 300,
    'time_remaining_seconds': 287,
    'winner': None,  # None, 'players', or 'time'
    'recent_events': [
        {'timestamp': 2.45, 'message': 'P1 joined...'},
        ...
    ]
}
```

---

## Example Communication Flow

### Join Sequence
```
Client                              Server
  │                                   │
  ├─ Connect to port 37001 ────────-─→│
  │                                   │
  ├─ Send {client_token: "uuid"} ────→│
  │                                   │ (BroadcastAcceptor receives)
  │                                   │ (Add to ClientRegistry)
  │                                   │
  ├─ [Start BroadcastListener]        │
  │                                   │
  ├─ Connect to port 37000 ───────-──→│
  │                                   │ (GameServerSkeleton receives)
  ├─ Send {type: "join", ...} ─────-─→│
  │                                   │ (Wait for client in registry)
  │                                   │ (Call join_player)
  │                                   │ (Send WELCOME via broadcast)
  │←─ WELCOME {board, state} ───────-─│
  │  (BroadcastListener receives)     │
```

### Move Sequence
```
Client                              Server
  │                                   │
  ├─ Send {type: "move", ...} ─────-─→│
  │                                   │ (GameServerSkeleton)
  │                                   │ (game_service.move())
  │                                   │ (DataStore validates & updates)
  │←─ COMMAND_RESULT {board} ──────-──│
  │  (BroadcastListener receives)     │
  │                                   │
  │ (Every 5 seconds)                 │
  │←─ BROADCAST_STATE {board} ─────--─│
  │  (From BroadcastSender thread)    │
```

---


## Key Design Insights

1. **Asymmetric Communication**: Server only sends via broadcast, simplifying client handling and enabling easy player broadcasting.

2. **Token-Based Handshake**: Using UUIDs to correlate broadcast and command channels allows flexibility in connection order.

3. **Thread-Safe State**: All game mutations protected by a single lock in DataStore, ensuring consistency despite concurrent players.

4. **Separation of Concerns**:
   - Protocol: Handles low-level framing
   - DataStore: Manages state and validation
   - GameService: Provides high-level API
   - Network components: Handle I/O only

5. **Periodic Broadcasting**: Rather than responding to each action, the server periodically pushes the entire state, reducing protocol complexity.

6. **Event Logging**: Circular buffer of recent events provides game history for debugging and player feedback.

7. **Graceful Cleanup**: All threads handle disconnection gracefully, cleaning up resources even in error cases.

---

## Configuration

Modify `shared/constants.py` to adjust:
- Board size: `GRID_WIDTH`, `GRID_HEIGHT`
- Player limit: `MAX_PLAYERS`
- Time limit: `TIME_LIMIT_SECONDS`
- Object positions: `FLOWERS`, `GARDEN_SPOTS`, `OBSTACLES`
- Broadcast interval: Pass `interval=` to `BroadcastSender` in `machine.py`

---

## Extensibility

Future enhancements:

- **Difficulty Levels**: Use configuration profiles
- **GUI Client**: Replace CLI with PyGame
- **Game Lobby**: Add pre-game room management

Extras:
- **Statistics**: Track player stats across games
- **Authentication**: Add login system
- **Chat**: Enable player communication