"""
Game service layer - facade for game operations.

Provides a high-level API for game actions, delegating all state management
to the DataStore. This layer could be extended for business logic, validation,
or action logging beyond the DataStore's scope.

Each method maps a game command to the corresponding DataStore operation
and returns the result tuple (success: bool, message: str).
"""


class GameService:
    """Service layer for game operations."""

    def __init__(self, data_store):
        """
        Initialize the game service with a DataStore instance.
        
        Args:
            data_store (DataStore): The centralized game state management
        """
        self.data_store = data_store

    def join_player(self, player_name, client_address):
        """
        Register a new player joining the game.
        
        Creates a new player in the data store with the given name
        and client address information.
        
        Args:
            player_name (str): The player's chosen name
            client_address (tuple): (host, port) of the client connection
        
        Returns:
            tuple: (player_id, player_info_dict) where player_info includes
                   position, has_flower, connected status, and name
        
        Raises:
            ValueError: If maximum players already reached
        """
        player_id, player_info = self.data_store.add_player(client_address)
        player_info["name"] = player_name
        if player_id in self.data_store.players:
            self.data_store.players[player_id]["name"] = player_name
        return player_id, player_info

    def move(self, player_id, direction):
        """
        Move a player in the specified direction.
        
        Args:
            player_id (str): The player ID
            direction (str): 'up', 'down', 'left', or 'right'
        
        Returns:
            tuple: (success: bool, message: str)
        """
        return self.data_store.move_player(player_id, direction)

    def pick(self, player_id):
        """
        Pick up a flower at the player's current location.
        
        Args:
            player_id (str): The player ID
        
        Returns:
            tuple: (success: bool, message: str)
        """
        return self.data_store.pick_flower(player_id)

    def plant(self, player_id):
        """
        Plant a carried flower at the player's current location.
        
        Args:
            player_id (str): The player ID
        
        Returns:
            tuple: (success: bool, message: str)
        """
        return self.data_store.plant_flower(player_id)

    def get_state(self):
        """
        Get the current public game state.
        
        Returns:
            dict: Complete game state including players, flowers,
                  garden spots, time, winner, and recent events
        """
        return self.data_store.get_public_state()

    def get_board(self):
        """
        Get the ASCII board representation of the current game state.
        
        Returns:
            str: Formatted board for terminal display
        """
        return self.data_store.render_board()

    def disconnect(self, player_id):
        """
        Remove a player from the game.
        
        Args:
            player_id (str): The player ID to disconnect
        """
        self.data_store.remove_player(player_id)