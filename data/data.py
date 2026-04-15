import threading
import time
from copy import deepcopy

from data.constants import GRID_WIDTH, GRID_HEIGHT, MAX_PLAYERS, TIME_LIMIT_SECONDS, FLOWERS, GARDEN_SPOTS, OBSTACLES


class DataStore:
    def __init__(self):
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
        self.game_started_at = time.time()
        self.time_limit_seconds = 300
        self.winner = None

    def _free_start_position(self):
        candidates = [
            (0, 1), (1, 0), (2, 0), (3, 0),
            (0, 4), (1, 5), (4, 5), (5, 4)
        ]
        occupied = {tuple(player['position']) for player in self.players.values()}
        blocked = set(self.obstacles) | set(self.flowers) | set(self.garden_spots.keys())
        for pos in candidates:
            if pos not in occupied and pos not in blocked:
                return pos
        for y in range(self.height):
            for x in range(self.width):
                pos = (x, y)
                if pos not in occupied and pos not in blocked:
                    return pos
        raise RuntimeError('No free start positions available.')

    def add_player(self, client_address):
        with self.lock:
            if len(self.players) >= self.max_players:
                raise ValueError('Maximum number of players reached.')
            player_id = f'P{self.next_player_id}'
            self.next_player_id += 1
            start_pos = self._free_start_position()
            self.players[player_id] = {
                'position': start_pos,
                'has_flower': False,
                'connected': True,
                'address': f'{client_address[0]}:{client_address[1]}'
            }
            self._log_event(f'{player_id} joined the garden at {start_pos}.')
            return player_id, deepcopy(self.players[player_id])

    def remove_player(self, player_id):
        with self.lock:
            if player_id in self.players:
                self.players[player_id]['connected'] = False
                self._log_event(f'{player_id} left the game.')

    def _log_event(self, message):
        self.event_log.append({
            'timestamp': round(time.time() - self.game_started_at, 2),
            'message': message,
        })
        self.event_log = self.event_log[-15:]

    def _inside(self, position):
        x, y = position
        return 0 <= x < self.width and 0 <= y < self.height

    def _occupied_by_player(self, position, exclude_player=None):
        for pid, player in self.players.items():
            if pid != exclude_player and tuple(player['position']) == position and player['connected']:
                return True
        return False

    def move_player(self, player_id, direction):
        deltas = {
            'up': (0, -1),
            'down': (0, 1),
            'left': (-1, 0),
            'right': (1, 0),
        }
        with self.lock:
            if self.winner:
                return False, f'Game already finished. Winner: {self.winner}'
            if player_id not in self.players:
                return False, 'Unknown player.'
            if direction not in deltas:
                return False, 'Direction must be up/down/left/right.'
            x, y = self.players[player_id]['position']
            dx, dy = deltas[direction]
            new_pos = (x + dx, y + dy)
            if not self._inside(new_pos):
                return False, 'Move rejected: outside the map.'
            if new_pos in self.obstacles:
                return False, 'Move rejected: obstacle on that tile.'
            if self._occupied_by_player(new_pos, exclude_player=player_id):
                return False, 'Move rejected: another player is already there.'
            self.players[player_id]['position'] = new_pos
            self._log_event(f'{player_id} moved {direction} to {new_pos}.')
            return True, f'{player_id} moved {direction} to {new_pos}.'

    def pick_flower(self, player_id):
        with self.lock:
            if self.winner:
                return False, f'Game already finished. Winner: {self.winner}'
            player = self.players.get(player_id)
            if not player:
                return False, 'Unknown player.'
            pos = tuple(player['position'])
            if player['has_flower']:
                return False, 'You already carry a flower.'
            if pos not in self.flowers:
                return False, 'There is no flower on your current tile.'
            self.flowers.remove(pos)
            player['has_flower'] = True
            self._log_event(f'{player_id} picked a flower at {pos}.')
            return True, f'{player_id} picked a flower at {pos}.'

    def plant_flower(self, player_id):
        with self.lock:
            if self.winner:
                return False, f'Game already finished. Winner: {self.winner}'
            player = self.players.get(player_id)
            if not player:
                return False, 'Unknown player.'
            pos = tuple(player['position'])
            if not player['has_flower']:
                return False, 'You do not carry a flower.'
            if pos not in self.garden_spots:
                return False, 'This tile is not a garden spot.'
            if self.garden_spots[pos]:
                return False, 'This garden spot is already occupied.'
            self.garden_spots[pos] = True
            player['has_flower'] = False
            self._log_event(f'{player_id} planted a flower at {pos}.')
            if all(self.garden_spots.values()):
                self.winner = 'players'
                self._log_event('All flowers were planted. Cooperative victory!')
            return True, f'{player_id} planted a flower at {pos}.'

    def get_public_state(self):
        with self.lock:
            elapsed = int(time.time() - self.game_started_at)
            remaining = max(0, self.time_limit_seconds - elapsed)
            if remaining == 0 and not self.winner:
                self.winner = 'time'
                self._log_event('Time limit reached. Players lost the game.')
            return {
                'grid_size': [self.width, self.height],
                'players': {
                    pid: {
                        'position': list(player['position']),
                        'has_flower': player['has_flower'],
                        'connected': player['connected'],
                    }
                    for pid, player in self.players.items()
                },
                'flowers': [list(pos) for pos in self.flowers],
                'garden_spots': [
                    {'position': list(pos), 'occupied': occupied}
                    for pos, occupied in self.garden_spots.items()
                ],
                'obstacles': [list(pos) for pos in self.obstacles],
                'time_limit_seconds': self.time_limit_seconds,
                'time_remaining_seconds': remaining,
                'winner': self.winner,
                'recent_events': deepcopy(self.event_log[-8:]),
            }

    def render_board(self):
        with self.lock:
            board = [['.' for _ in range(self.width)] for _ in range(self.height)]
            for x, y in self.obstacles:
                board[y][x] = '#'
            for x, y in self.flowers:
                board[y][x] = 'F'
            for (x, y), occupied in self.garden_spots.items():
                board[y][x] = 'G' if not occupied else '*'
            for pid, player in self.players.items():
                if not player['connected']:
                    continue
                x, y = player['position']
                base_token = chr(ord('A') + int(pid[1:]) - 1)
                token = base_token.lower() if player['has_flower'] else base_token
                board[y][x] = token
            lines = ['   ' + ' '.join(str(i) for i in range(self.width))]
            for idx, row in enumerate(board):
                lines.append(f'{idx}  ' + ' '.join(row))
            return '\n'.join(lines)
