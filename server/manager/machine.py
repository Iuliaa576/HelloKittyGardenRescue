"""
Game server machine - main orchestrator for the distributed game.

The Machine class is the entry point for the server. It:
1. Creates and manages the game state (DataStore)
2. Manages the client registry (broadcast connections)
3. Accepts incoming command connections from clients
4. Spawns a daemon thread for accepting broadcast connections
5. Starts the periodic broadcast sender thread

Communication Flow:
    - Each client connects with a command channel (to send actions)
    - Each client also establishes a broadcast channel (to receive updates)
    - A handshake ensures both connections are established before the
      player joins the game (token-based correlation)
    - GameServerSkeleton handles one command channel in each thread
    - BroadcastSender periodically sends state to all registered clients

Architecture:
    - One thread per client (GameServerSkeleton)
    - One broadcast sender thread (BroadcastSender)
    - One daemon thread accepting broadcast connections
    - Main thread accepts command connections
"""

import socket
import threading

from shared.constants import SERVER_HOST, PORT, BROADCAST_PORT
from shared.protocol import receive_packet
from server.core.data_store import DataStore
from server.core.game_service import GameService
from server.manager.client_registry import ClientRegistry
from server.network.broadcast_sender import BroadcastSender
from server.network.game_server_skeleton import GameServerSkeleton


class Machine:
    """Main game server orchestrator."""

    def __init__(self):
        """Initialize the game server with all required components."""
        self.data_store = DataStore()                   # Centralized game state
        self.game_service = GameService(self.data_store)  # Service layer
        self.client_registry = ClientRegistry()          # Broadcast connection management

    def _accept_broadcast_clients(self):
        """
        Accept incoming broadcast channel connections from clients.
        
        This runs in a daemon thread. Each client first opens this connection
        and sends their token, then opens the command connection.
        
        The token is used to correlate the two connections and ensure
        the player only joins after both channels are established.
        
        Runs indefinitely, accepting new broadcast connections.
        """
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((SERVER_HOST, BROADCAST_PORT))
        s.listen(5)

        print("[SERVER] Waiting for broadcast clients on port:", BROADCAST_PORT)

        while True:
            conn, addr = s.accept()
            print("[SERVER] Broadcast socket connected:", addr)

            try:
                data = receive_packet(conn)
                token = data.get("client_token")

                if not token:
                    conn.close()
                    continue

                self.client_registry.add_client(token, conn)
                print("[SERVER] Registered broadcast client token:", token)

            except Exception as exc:
                print("[SERVER] Failed broadcast registration:", exc)
                conn.close()

    def execute(self):
        """
        Start the game server.
        
        Initializes:
        1. Daemon thread for accepting broadcast connections
        2. BroadcastSender thread for periodic state updates
        3. Main server socket for accepting command connections
        
        Runs indefinitely, spawning a new GameServerSkeleton thread
        for each incoming client command connection.
        """
        # Start daemon thread for broadcast connections
        threading.Thread(target=self._accept_broadcast_clients, daemon=True).start()

        # Start periodic broadcast sender
        broadcast_thread = BroadcastSender(self.client_registry, self.game_service, interval=5)
        broadcast_thread.start()

        # Main command server socket
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((SERVER_HOST, PORT))
        s.listen(5)

        print("[SERVER] Main server started on port:", PORT)

        # Accept command connections from clients indefinitely
        while True:
            conn, addr = s.accept()
            print("[SERVER] Command client connected:", addr)
            process = GameServerSkeleton(
                conn,
                addr,
                self.game_service,
                self.client_registry,
            )
            process.start()