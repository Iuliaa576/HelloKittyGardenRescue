# Hello Kitty Garden Rescue

Distributed Systems Project — 2025/2026

## Overview

Hello Kitty Garden Rescue is a cooperative multiplayer distributed game developed in Python for the Distributed Systems course.

Players must collaborate to collect flowers scattered around the map and plant them in the designated garden spots before the countdown timer expires.

The game follows a distributed client-server architecture and supports multiple concurrent players connected through sockets.

The graphical interface was implemented using PyGame.

---

# Game Features

* Cooperative multiplayer gameplay
* Distributed client-server architecture
* Real-time shared game state
* Socket-based communication
* Concurrent player handling using threads
* Thread-safe shared game state using locks
* Lobby screen with character selection
* PyGame graphical interface
* Terminal interface support
* Multiple Hello Kitty characters
* Countdown timer
* Obstacles and interactive objects
* Victory and defeat states
* Waiting-for-players system

---

# Game Objective

Players must:

1. Move around the map
2. Pick up flowers
3. Carry flowers to garden spots
4. Plant all flowers before time runs out

The game is cooperative:
all players work together to complete the garden.

---

# Technologies Used

* Python 3
* PyGame
* Python sockets
* Python threading

---

# Distributed Architecture

The project is organized into three main packages:

## Client

Responsible for:

* Graphical interface
* Terminal interface
* Sending player commands
* Receiving updates from the server

Important components:

* `GameClientStub`
* `BroadcastListener`
* `pygame_interaction.py`

---

## Server

Responsible for:

* Game logic
* Shared game state
* Synchronization
* Player management
* Timer management
* Broadcasting updates

Important components:

* `GameServerSkeleton`
* `DataStore`
* `GameService`

---

## Shared

Contains:

* Protocol definitions
* Message types
* Shared constants

---

# Communication Model

The game uses a hybrid communication structure based on two separate socket connections.

## Connection Scheme

```text
+-------------------+
|   Player Client   |
|-------------------|
| PyGame / Terminal |
| UI                |
+---------+---------+
          |
          |
          v
+-------------------+
|  GameClientStub   |
+---------+---------+
          |
          | Command Socket
          |
          v
+-------------------+
| GameServerSkeleton|
+---------+---------+
          |
          v
+-------------------+
|    GameService    |
+---------+---------+
          |
          v
+-------------------+
|     DataStore     |
| (shared game      |
|      state)       |
+-------------------+


+-------------------+
| BroadcastListener |
+---------+---------+
          ^
          |
          | Broadcast Socket
          |
+---------+---------+
|       Server      |
+-------------------+
```

The client establishes:

1. A command connection used to send player actions to the server
2. A broadcast connection used to receive updated game state and events from the server

The server processes commands, updates the centralized game state, and broadcasts the updated state to all connected players.

## Command Channel

Clients send commands to the server:

* MOVE
* PICK
* PLANT
* STATE
* DISCONNECT

## Broadcast Channel

The server broadcasts:

* Updated game state
* Events
* Timer updates
* Victory/defeat state

---

# Concurrency

The server supports multiple simultaneous players.

Concurrency is handled using:

* Python threads
* Thread synchronization using `threading.Lock()`

The centralized game state is protected against concurrent access.

---

# Game State Structure

The server maintains a centralized game state containing:

* Players
* Player positions
* Flowers
* Garden spots
* Obstacles
* Timer information
* Connected players
* Game events
* Winner state

This state is stored in:

```text
server/core/data_store.py
```

---

# Map

The game uses a 10x10 grid.

The map contains:

* Flowers
* Obstacles
* Garden spots
* Multiple player spawn locations

---

# Characters

Players may choose one of the following characters:

* Hello Kitty
* Kuromi
* Cinnamoroll
* My Melody

---

# Game Flow

1. Players open the client
2. Players enter a username
3. Players choose a character
4. Players connect to the server
5. The game waits until at least 2 players are connected
6. The game starts automatically
7. Players cooperate to complete the garden
8. The game ends with:

* Victory (all flowers planted)
* Defeat (time expired)

---

# Running the Project

## Install Dependencies

```bash
pip install pygame
```

---

## Start the Server

```bash
python -m server
```

---

## Start the Graphical Client

```bash
python -m client.ui.pygame_interaction --host 127.0.0.1
```

---

## Start the Terminal Client

```bash
python -m client
```

---

# Controls

## Movement

* Arrow Keys
* OR WASD

## Actions

* P → Pick flower
* L → Plant flower
* SPACE → Request state
* ESC / Q → Exit game

---

# Final Notes

The game was designed to satisfy the requirements of the Distributed Systems project:

* Independent client and server processes
* Socket communication
* Middleware-like abstraction using stubs and skeletons
* Shared distributed game state
* Concurrent access management
* Graphical interface using PyGame
* Multiplayer support across different computers

The project demonstrates the practical application of distributed systems concepts in an interactive multiplayer environment.
