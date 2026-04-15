import json
import threading


class BroadcastReceiver(threading.Thread):
    def __init__(self, connection):
        super().__init__(daemon=True)
        self.connection = connection

    def receive_exact(self, n):
        data = b''
        while len(data) < n:
            chunk = self.connection.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Broadcast connection closed.")
            data += chunk
        return data

    def receive_packet(self):
        raw_length = self.receive_exact(4)
        length = int.from_bytes(raw_length, 'big')
        raw_data = self.receive_exact(length)
        return json.loads(raw_data.decode())

    def run(self):
        while True:
            try:
                data = self.receive_packet()
                msg_type = data.get("type")

                print("\n=== Broadcast message ===")

                if msg_type == "welcome":
                    print(data.get("message"))
                    print("Assigned player id:", data.get("player_id"))
                    if data.get("board"):
                        print(data["board"])

                elif msg_type == "command_result":
                    print(data.get("message"))
                    if data.get("board"):
                        print(data["board"])

                    state = data.get("state", {})
                    print("Time remaining:", state.get("time_remaining_seconds"))
                    print("Winner:", state.get("winner"))

                elif msg_type == "broadcast_state":
                    if data.get("board"):
                        print(data["board"])

                    state = data.get("state", {})
                    print("Time remaining:", state.get("time_remaining_seconds"))
                    print("Winner:", state.get("winner"))

                    events = state.get("recent_events", [])
                    if events:
                        print("Recent events:")
                        for event in events[-3:]:
                            print(f"  t={event['timestamp']}: {event['message']}")

                elif msg_type == "bye":
                    print(data.get("message"))

                else:
                    print("Unknown broadcast message:", data)

                print("=========================\n")

            except Exception as exc:
                print("Broadcast receiver stopped:", exc)
                break