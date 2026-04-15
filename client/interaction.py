import json
import socket
import uuid
import time

from client import COMMAND_SIZE, SERVER_ADDRESS, PORT, BROADCAST_PORT
from client.broadcast_receiver import BroadcastReceiver


def send_str(conn, value):
    conn.sendall(value.ljust(COMMAND_SIZE).encode())


def send_packet(conn, payload):
    data = json.dumps(payload).encode()
    conn.sendall(len(data).to_bytes(4, 'big') + data)


class Interaction:
    def _print_help(self):
        print("Commands:")
        print("  move up|down|left|right")
        print("  pick")
        print("  plant")
        print("  state")
        print("  stop")
        print("  help")

    def execute(self):
        token = str(uuid.uuid4())

        # 1) Broadcast connection
        broadcast_conn = socket.socket()
        broadcast_conn.connect((SERVER_ADDRESS, BROADCAST_PORT))
        send_packet(broadcast_conn, {"client_token": token})

        receiver = BroadcastReceiver(broadcast_conn)
        receiver.start()

        # Give the server a tiny moment to register the broadcast client
        time.sleep(0.2)

        # 2) Command connection
        conn = socket.socket()
        conn.connect((SERVER_ADDRESS, PORT))
        send_packet(conn, {"client_token": token})

        self._print_help()

        try:
            while True:
                cmd = input("Command: ").strip().lower()
                if not cmd:
                    continue

                parts = cmd.split()

                if parts[0] == "help":
                    self._print_help()
                    continue

                elif parts[0] == "move" and len(parts) == 2:
                    send_str(conn, "move")
                    send_packet(conn, {"direction": parts[1]})

                elif parts[0] in ["pick", "plant", "state"]:
                    send_str(conn, parts[0])

                elif parts[0] == "stop":
                    send_str(conn, "stop")
                    break

                else:
                    print("Invalid command")
        finally:
            conn.close()
            broadcast_conn.close()