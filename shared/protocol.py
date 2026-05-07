"""
Shared socket communication protocol utilities.

This module implements JSON packet serialization and a length-prefixed
communication protocol for reliable client-server messaging.
"""

import json
from shared.constants import PACKET_LENGTH_SIZE


def receive_exact(conn, n_bytes):
    """
    Receive an exact number of bytes from a socket connection.
    """
    data = b""
    while len(data) < n_bytes:
        chunk = conn.recv(n_bytes - len(data))
        if not chunk:
            raise ConnectionError("Connection closed while receiving data.")
        data += chunk
    return data


def send_packet(conn, payload):
    """
    Serialize and send a packet through a socket connection.
    """
    data = json.dumps(payload).encode()
    conn.sendall(len(data).to_bytes(PACKET_LENGTH_SIZE, "big") + data)


def receive_packet(conn):
    """
    Receive and deserialize a packet from a socket connection.
    """
    raw_length = receive_exact(conn, PACKET_LENGTH_SIZE)
    length = int.from_bytes(raw_length, "big")
    raw_data = receive_exact(conn, length)
    return json.loads(raw_data.decode())