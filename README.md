# Hello Kitty Garden Rescue - Distributed Multiplayer Game Prototype

This project is a **distributed multiplayer game prototype (non-graphical)** developed for the intermediate presentation.

It follows the required structure from the laboratory:
- client-server architecture
- support for multiple clients
- shared game state managed on the server
- communication via sockets
- broadcast updates for synchronization

---

## 1. Architecture

### Communication Model
Hybrid approach:
- **Client-Server (request/response):**
  Used for player actions
- **Server Broadcast (publish updates):**
  Used to send game state updates to all clients

### Ports
- Main communication: `PORT = 37000`
- Broadcast updates: `BROADCAST_PORT = 37001`

### Concurrency
- One thread per connected client
- One broadcast thread (server → clients)
- One thread for accepting broadcast connections
- Shared state protected using `threading.Lock`

---

## 2. Communication Protocol

### What information is sent by each player?

Each player sends:
- A command string (fixed size):
  - `move`
  - `pick`
  - `plant`
  - `state`
  - `stop`
- Additional data (only when needed):
  - For `move`:  
    ```json
    { "direction": "up", "down", "left", "right"}
    ```

So, players only send **actions**, not full game state.

---

### What information is returned by the server?

The server responds with a JSON packet containing:
- `type`: response type
- `ok`: success or failure
- `message`: description of the result
- `player_id`: identifier of the player
- `state`: full public game state
- `board`: terminal representation of the map

Additionally:
- When a player connects:
  - A **welcome message** with initial state is sent
- Periodically:
  - The server **broadcasts updates** to all clients with:
    - current game state
    - board rendering
    - recent events

---

## 3. Game Machine (Server Side)

The server acts as the **game engine**, implemented using:

### Main Components
- `Machine`
  - Accepts clients
  - Starts threads
  - Coordinates the system
- `ProcessClient`
  - Handles each player interaction
- `BroadcastThread`
  - Sends updates to all clients
- `DataStore`
  - Centralized game state (acts as in-memory database)

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
- Game ends:
  - **Win:** all garden spots are filled
  - **Lose:** time runs out

---

### Game Parameters
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

All access is synchronized using a **thread lock**.

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
- Server-client communication working  
- Broadcast updates to all players  
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
- Optional manager component (if required)  

---