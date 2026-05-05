"""
Low-level socket communication protocol for reliable message delivery.

Implements a length-prefixed message protocol using JSON serialization:
- Each message is prefixed with a 4-byte big-endian length field
- The message body is the JSON-serialized payload
- Handles partial receives and ensures complete data transfer

This design ensures reliable, frame-based communication even over
unreliable TCP streams where recv() may return partial data.
"""

import json
from shared.constants import PACKET_LENGTH_SIZE


def receive_exact(conn, n_bytes):
    """
    Receive exactly n_bytes from a socket connection.
    
    Handles partial receives by looping until the full amount of data
    is received, ensuring reliable communication even if TCP breaks up
    the data into multiple packets.
    
    Args:
        conn: Socket connection object
        n_bytes (int): Exact number of bytes to receive
    
    Returns:
        bytes: The received data
    
    Raises:
        ConnectionError: If the connection closes before all data is received
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
    Send a JSON-serialized packet with length prefix.
    
    Serializes the payload to JSON, prepends a 4-byte big-endian length field,
    and sends it atomically using sendall() to ensure all data is sent.
    
    Packet format: [4-byte length][JSON payload]
    
    Args:
        conn: Socket connection object
        payload (dict): Message dictionary to send
    
    Raises:
        OSError: If sending fails due to connection issues
    """
    data = json.dumps(payload).encode()
    conn.sendall(len(data).to_bytes(PACKET_LENGTH_SIZE, "big") + data)


def receive_packet(conn):
    """
    Receive and deserialize a single JSON packet.
    
    Reads the 4-byte length prefix, then reads that many bytes,
    and finally deserializes the JSON payload.
    
    Returns:
        dict: The deserialized message payload
    
    Raises:
        ConnectionError: If the connection closes during receive
        json.JSONDecodeError: If the received data is not valid JSON
    """
    raw_length = receive_exact(conn, PACKET_LENGTH_SIZE)
    length = int.from_bytes(raw_length, "big")
    raw_data = receive_exact(conn, length)
    return json.loads(raw_data.decode())