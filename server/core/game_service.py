"""
Game service layer.

This module provides an abstraction layer between the server networking
components and the centralized game state stored in the DataStore.
"""


class GameService:

    def __init__(self, data_store):
        """Initialize the service layer with the shared data store."""
        self.data_store = data_store

    def join_player(self, player_name, character, client_address):
        """Register a new player in the game."""
        return self.data_store.add_player(player_name, character, client_address)

    def move(self, player_id, direction):
        """Process a player movement request."""
        return self.data_store.move_player(player_id, direction)

    def pick(self, player_id):
        """Process a flower pickup request."""
        return self.data_store.pick_flower(player_id)

    def plant(self, player_id):
        """Process a flower planting request."""
        return self.data_store.plant_flower(player_id)

    def get_state(self):
        """Return the current public game state."""
        return self.data_store.get_public_state()

    def get_board(self):
        """Return the text representation of the game board."""
        return self.data_store.render_board()

    def disconnect(self, player_id):
        """Remove a disconnected player from the game."""
        self.data_store.remove_player(player_id)