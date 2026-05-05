"""
Server module for Hello Kitty Garden Rescue.

This package contains the server-side implementation of the distributed game:
    - Core: Game logic and state management (server.core)
        - DataStore: Centralized game state with thread-safe access
        - GameService: Service layer for game operations
    - Manager: Server orchestration (server.manager)
        - Machine: Main server entry point and coordination
        - ClientRegistry: Broadcast connection management
    - Network: Socket communication (server.network)
        - GameServerSkeleton: Handler for client command channels
        - BroadcastSender: Periodic state broadcaster

The server manages game state, validates actions, and broadcasts updates
to all connected clients. Supports up to 4 concurrent players.

Entry point: python -m server

Listens on:
    - PORT 37000: Command channel (client → server)
    - PORT 37001: Broadcast channel (server → client)
"""
