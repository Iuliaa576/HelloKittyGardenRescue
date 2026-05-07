"""
Centralized game state management.

This module stores and manages the shared game state on the server side.
It handles:
- Player management
- Movement validation
- Flower pickup and planting
- Game timer and victory conditions
- Event logging
- Thread-safe concurrent access
"""

import threading
import time
from copy import deepcopy

from shared.constants import (
    GRID_WIDTH,
    GRID_HEIGHT,
    MAX_PLAYERS,
    TIME_LIMIT_SECONDS,
    FLOWERS,
    GARDEN_SPOTS,
    OBSTACLES,
    MIN_PLAYERS_TO_START,
)


class DataStore:

    def __init__(self):
        """Initialize the shared game state and synchronization resources."""
        self.lock = threading.Lock()

        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT

        self.max_players = MAX_PLAYERS
        self.time_limit_seconds = TIME_LIMIT_SECONDS

        self.flowers = list(FLOWERS)
        self.garden_spots = dict(GARDEN_SPOTS)
        self.obstacles = list(OBSTACLES)

        self.players = {}
        self.next_player_id = 1

        self.event_log = []

        self.game_started = False
        self.game_started_at = None
        self.game_finished_at = None

        self.winner = None

    def _free_start_position(self):
        """Find and return an available player spawn position."""
        candidates = [
            (0, 0),
            (1, 0),
            (2, 0),
            (7, 0),
            (8, 0),
            (9, 0),
            (0, 8),
            (1, 9),
            (8, 9),
            (9, 8),
        ]

        occupied = {
            tuple(player["position"])
            for player in self.players.values()
            if player["connected"]
        }

        blocked = set(self.obstacles) | set(self.flowers) | set(self.garden_spots.keys())

        for pos in candidates:
            if pos not in occupied and pos not in blocked:
                return pos

        for y in range(self.height):
            for x in range(self.width):
                pos = (x, y)
                if pos not in occupied and pos not in blocked:
                    return pos

        raise RuntimeError("No free start positions available.")


    def add_player(self, player_name, character, client_address):
        """Add a new player to the game and assign a starting position."""
        with self.lock:
            if len(self.players) >= self.max_players:
                raise ValueError("Maximum number of players reached.")

            player_id = f"P{self.next_player_id}"
            self.next_player_id += 1

            start_pos = self._free_start_position()

            self.players[player_id] = {
                "position": start_pos,
                "has_flower": False,
                "connected": True,
                "address": f"{client_address[0]}:{client_address[1]}",
                "name": player_name,
                "character": character,
            }

            self._log_event(
                f"{player_name} ({player_id}) joined as {character} at {start_pos}."
            )

            self._try_start_game()

            return player_id, self.players[player_id].copy()

    def remove_player(self, player_id):
        """Remove a player from the game state."""
        with self.lock:
            if player_id in self.players:
                name = self.players[player_id].get("name", player_id)
                self._log_event(f"{name} ({player_id}) left the game.")
                del self.players[player_id]

    def _log_event(self, message):
        """Store a timestamped game event in the event log."""
        if self.game_started_at is None:
            timestamp = 0
        else:
            timestamp = round(time.time() - self.game_started_at, 2)

        self.event_log.append(
            {
                "timestamp": timestamp,
                "message": message,
            }
        )
        self.event_log = self.event_log[-15:]

    def _connected_player_count(self):
        """Return the number of currently connected players."""
        return sum(1 for player in self.players.values() if player["connected"])

    def _try_start_game(self):
        """Start the game automatically when enough players are connected."""
        if not self.game_started and self._connected_player_count() >= MIN_PLAYERS_TO_START:
            self.game_started = True
            self.game_started_at = time.time()
            self._log_event("Minimum players reached. Game started!")

    def _inside(self, position):
        """Check whether a position is inside the game grid."""
        x, y = position
        return 0 <= x < self.width and 0 <= y < self.height

    def _occupied_by_player(self, position, exclude_player=None):
        """Check whether a tile is occupied by another connected player."""
        for pid, player in self.players.items():
            if (
                pid != exclude_player
                and tuple(player["position"]) == position
                and player["connected"]
            ):
                return True

        return False

    def move_player(self, player_id, direction):
        """Attempt to move a player in the specified direction."""
        deltas = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0),
        }

        with self.lock:
            if not self.game_started:
                return False, f"Waiting for at least {MIN_PLAYERS_TO_START} players to start."

            if self.winner:
                return False, f"Game already finished. Winner: {self.winner}"

            if player_id not in self.players:
                return False, "Unknown player."

            if direction not in deltas:
                return False, "Direction must be up/down/left/right."

            x, y = self.players[player_id]["position"]
            dx, dy = deltas[direction]
            new_pos = (x + dx, y + dy)

            if not self._inside(new_pos):
                return False, "Move rejected: outside the map."

            if new_pos in self.obstacles:
                return False, "Move rejected: obstacle on that tile."

            if self._occupied_by_player(new_pos, exclude_player=player_id):
                return False, "Move rejected: another player is already there."

            self.players[player_id]["position"] = new_pos

            name = self.players[player_id].get("name", player_id)
            self._log_event(f"{name} moved {direction} to {new_pos}.")

            return True, f"{player_id} moved {direction} to {new_pos}."

    def pick_flower(self, player_id):
        """Allow a player to pick up a flower from the current tile."""
        with self.lock:
            if not self.game_started:
                return False, f"Waiting for at least {MIN_PLAYERS_TO_START} players to start."

            if self.winner:
                return False, f"Game already finished. Winner: {self.winner}"

            player = self.players.get(player_id)

            if not player:
                return False, "Unknown player."

            pos = tuple(player["position"])

            if player["has_flower"]:
                return False, "You already carry a flower."

            if pos not in self.flowers:
                return False, "There is no flower on your current tile."

            self.flowers.remove(pos)
            player["has_flower"] = True

            name = player.get("name", player_id)
            self._log_event(f"{name} picked a flower at {pos}.")

            return True, f"{player_id} picked a flower at {pos}."

    def plant_flower(self, player_id):
        """Allow a player to plant a carried flower in a garden spot."""
        with self.lock:
            if not self.game_started:
                return False, f"Waiting for at least {MIN_PLAYERS_TO_START} players to start."

            if self.winner:
                return False, f"Game already finished. Winner: {self.winner}"

            player = self.players.get(player_id)

            if not player:
                return False, "Unknown player."

            pos = tuple(player["position"])

            if not player["has_flower"]:
                return False, "You do not carry a flower."

            if pos not in self.garden_spots:
                return False, "This tile is not a garden spot."

            if self.garden_spots[pos]:
                return False, "This garden spot is already occupied."

            self.garden_spots[pos] = True
            player["has_flower"] = False

            name = player.get("name", player_id)
            self._log_event(f"{name} planted a flower at {pos}.")

            if all(self.garden_spots.values()):
                self.winner = "players"
                self.game_finished_at = time.time()
                self._log_event("All flowers were planted. Cooperative victory!")

            return True, f"{player_id} planted a flower at {pos}."

    def get_public_state(self):
        """Return the public synchronized game state for clients."""
        with self.lock:
            connected_players = self._connected_player_count()

            if not self.game_started:
                remaining = self.time_limit_seconds
            else:
                if self.game_finished_at is not None:
                    elapsed = int(self.game_finished_at - self.game_started_at)
                else:
                    elapsed = int(time.time() - self.game_started_at)

                remaining = max(0, self.time_limit_seconds - elapsed)

                if remaining == 0 and not self.winner:
                    self.winner = "time"
                    self.game_finished_at = time.time()
                    remaining = 0
                    self._log_event("Time limit reached. Players lost the game.")

            return {
                "grid_size": [self.width, self.height],
                "players": {
                    pid: {
                        "position": list(player["position"]),
                        "has_flower": player["has_flower"],
                        "connected": player["connected"],
                        "name": player.get("name", pid),
                        "character": player.get("character", "hello_kitty"),
                    }
                    for pid, player in self.players.items()
                },
                "flowers": [list(pos) for pos in self.flowers],
                "garden_spots": [
                    {"position": list(pos), "occupied": occupied}
                    for pos, occupied in self.garden_spots.items()
                ],
                "obstacles": [list(pos) for pos in self.obstacles],
                "time_limit_seconds": self.time_limit_seconds,
                "time_remaining_seconds": remaining,
                "game_started": self.game_started,
                "connected_players": connected_players,
                "min_players_to_start": MIN_PLAYERS_TO_START,
                "winner": self.winner,
                "recent_events": deepcopy(self.event_log[-8:]),
            }

    def render_board(self):
        """Generate a text-based representation of the game board."""
        with self.lock:
            board = [["." for _ in range(self.width)] for _ in range(self.height)]

            for x, y in self.obstacles:
                board[y][x] = "#"

            for x, y in self.flowers:
                board[y][x] = "F"

            for (x, y), occupied in self.garden_spots.items():
                board[y][x] = "G" if not occupied else "*"

            for pid, player in self.players.items():
                if not player["connected"]:
                    continue

                x, y = player["position"]
                base_token = chr(ord("A") + int(pid[1:]) - 1)
                token = base_token.lower() if player["has_flower"] else base_token
                board[y][x] = token

            lines = ["   " + " ".join(str(i) for i in range(self.width))]

            for idx, row in enumerate(board):
                lines.append(f"{idx}  " + " ".join(row))

            return "\n".join(lines)