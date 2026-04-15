# Hello Kitty Garden Rescue - Distributed Multiplayer Game Prototype

This project is a **distributed multiplayer game prototype (non-graphical)** developed for the intermediate presentation.

It follows the required structure from the laboratory:
- client-server architecture  
- support for multiple clients  
- shared game state managed on the server  
- communication via sockets  
- broadcast-based synchronization  

---

## 1. Architecture

### Communication Model

Asymmetric communication model:

- **Client → Server (command channel):**  
  Used only for sending player actions to the server  

- **Server → Client (broadcast channel):**  
  Used for all outgoing messages, including:  
  - welcome messages  
  - command results  
  - periodic game state updates  
  - disconnect notifications  

This design removes synchronous request/response communication and ensures
that all server-to-client data is sent through a unified broadcast mechanism.

---

### Ports
- Main communication (commands): `PORT = 37000`  
- Broadcast updates: `BROADCAST_PORT = 37001`  

---

### Concurrency
- One thread per connected client  
- One broadcast thread (server → clients)  
- One thread for accepting broadcast connections  
- Shared state protected using `threading.Lock`  

---

## 2. Communication Protocol

### Client → Server Messages

Each player sends only actions:

- A command string (fixed size):  
  - `move`  
  - `pick`  
  - `plant`  
  - `state`  
  - `stop`  

- Additional data (only when needed):  

For `move`:
```json
{ "direction": "up"; "down"; "left"; "right" }
```

Players send only **actions**, not the full game state.

---

### Server → Client Messages (Broadcast Only)

All server responses and updates are sent through the broadcast channel.

#### 1. Welcome Message

Sent when a player connects:

```json
{
  "type": "welcome",
  "player_id": "P1",
  "message": "Welcome P1! Cooperative garden rescue started.",
  "player": { ... },
  "state": { ... },
  "board": "..."
}
```

#### 2. Command Result Message

Sent after processing a player action:

```json
{
  "type": "command_result",
  "ok": true,
  "message": "P1 moved up to (0, 0).",
  "player_id": "P1",
  "state": { ... },
  "board": "..."
}
```

#### 3. Periodic Broadcast State Update

Sent periodically to all connected clients:

```json
{
  "type": "broadcast_state",
  "state": { ... },
  "board": "..."
}
```

#### 4. Disconnect Message

Sent when a player leaves:

```json
{
  "type": "bye",
  "ok": true,
  "message": "P1 disconnected."
}
```

---

### Structure of the `state` Object

The `state` object contains the full public game state:

- `grid_size`: `[width, height]`  
- `players`: dictionary with:
  - `position`  
  - `has_flower`  
  - `connected`  
- `flowers`: list of positions  
- `garden_spots`: list of positions with occupation status  
- `obstacles`: list of positions  
- `time_limit_seconds`  
- `time_remaining_seconds`  
- `winner`: `null`, `"players"`, or `"time"`  
- `recent_events`: list of recent game actions  

---

## 3. Game Machine (Server Side)

The server acts as the **game engine**, implemented using:

### Main Components

- `Machine`  
  - Accepts clients  
  - Manages threads  
  - Coordinates communication  

- `ProcessClient`  
  - Handles each player's commands  
  - Processes actions  
  - Sends results through broadcast  

- `BroadcastThread`  
  - Periodically sends game state to all clients  

- `DataStore`  
  - Centralized game state (in-memory database)  
  - Contains all game logic and rules  

---

## 4. Game Description

### Objective

Players must **cooperate** to:
- collect all flowers  
- plant them in all garden spots  
before the time limit expires  

---

### Rules

- 2–4 players  
- Players can move:
  - `up`, `down`, `left`, `right`  
- Players can:
  - pick a flower (if on a flower tile)  
  - plant a flower (if on a garden spot)  
- Each player can carry **only one flower at a time**  

Game ends:
- **Win:** all garden spots are filled  
- **Lose:** time runs out  

---

### Game Parameters

The game parameters are defined as configuration constants to allow easy modification and future support for difficulty levels.

Current values:
- Grid size: `6 x 6`  
- Max players: `4`  
- Time limit: `300 seconds`  
- Obstacles: fixed positions  
- Flowers: fixed positions  
- Garden spots: fixed positions  

---

## 5. Data Structures

The game state is stored in `DataStore` using:

- `players: dict`
  - position, has_flower, connection status  
- `flowers: list[tuple]`  
- `garden_spots: dict[(x, y) → bool]`  
- `obstacles: list[tuple]`  
- `event_log: list[dict]`  
- `winner: str | None`  
- `time_remaining`  

All access is synchronized using a **thread lock** to ensure consistency in a multi-threaded environment.

---

## 6. Terminal Representation

Symbols:
- `.` → empty tile  
- `#` → obstacle  
- `F` → flower  
- `G` → empty garden spot  
- `*` → occupied garden spot  
- `A, B, C, D` → players (no flower)  
- `a, b, c, d` → players (carrying flower)  

---

## 7. Implemented Features (Current State)

- Multiple clients connected simultaneously  
- Command channel from client to server working  
- Broadcast-only communication from server to clients  
- Periodic game state updates  
- Targeted broadcast messages (welcome, command results, disconnect)  
- Centralized game state on server  
- Player actions:
  - move  
  - pick  
  - plant  
- Game rules enforced  
- Terminal visualization of the board  
- Event logging and time tracking  

---

## 8. Features in Development

- Graphical interface (PyGame)  
- Improved game design and visuals  
- Additional gameplay mechanics  
- Better UI/UX for players   
- Difficulty levels using configurable constants  
