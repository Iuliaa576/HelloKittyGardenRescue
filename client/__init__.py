"""
Client module for Hello Kitty Garden Rescue.

This package contains the client-side implementation of the distributed game:
    - UI: Interactive command-line interface (client.ui.interaction)
    - Network: Socket communication and message handling (client.network)
        - GameClientStub: Main client connection handler
        - BroadcastListener: Daemon thread for receiving server updates

Entry point: python -m client
"""
