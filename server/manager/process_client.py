import json
import threading

from server import COMMAND_SIZE


class ProcessClient(threading.Thread):
    def __init__(self, connection, address, data_store, client_list):
        super().__init__()
        self.connection = connection
        self.address = address
        self.data_store = data_store
        self.client_list = client_list
        self.player_id = None
        self.client_token = None

    def receive_exact(self, n_bytes):
        data = b''
        while len(data) < n_bytes:
            chunk = self.connection.recv(n_bytes - len(data))
            if not chunk:
                raise ConnectionError("Connection closed while receiving data.")
            data += chunk
        return data

    def receive_packet(self):
        raw_length = self.receive_exact(4)
        length = int.from_bytes(raw_length, 'big')
        raw_data = self.receive_exact(length)
        return json.loads(raw_data.decode())

    def receive_str(self):
        data = self.receive_exact(COMMAND_SIZE)
        return data.decode().strip()

    def run(self):
        print(self.address, "[THREAD] started")
        try:
            # First message on command socket = client token
            data = self.receive_packet()
            self.client_token = data.get("client_token")

            if not self.client_token:
                raise ValueError("Missing client_token on command channel.")

            # Wait until the broadcast socket for this token is registered
            ok = self.client_list.wait_for_client(self.client_token, timeout=5.0)
            if not ok:
                raise ConnectionError(
                    f"Broadcast channel not registered for token {self.client_token}"
                )

            self.player_id, player_info = self.data_store.add_player(self.address)
            print(self.address, "registered as", self.player_id, "with token", self.client_token)

            self.client_list.send_to_client(self.client_token, {
                "type": "welcome",
                "player_id": self.player_id,
                "message": f"Welcome {self.player_id}! Cooperative garden rescue started.",
                "player": player_info,
                "state": self.data_store.get_public_state(),
                "board": self.data_store.render_board(),
            })

            while True:
                op = self.receive_str()

                if op == "move":
                    payload = self.receive_packet()
                    ok, message = self.data_store.move_player(
                        self.player_id,
                        payload.get("direction", "").lower()
                    )

                elif op == "pick":
                    ok, message = self.data_store.pick_flower(self.player_id)

                elif op == "plant":
                    ok, message = self.data_store.plant_flower(self.player_id)

                elif op == "state":
                    ok, message = True, "State snapshot generated."

                elif op == "stop":
                    self.client_list.send_to_client(self.client_token, {
                        "type": "bye",
                        "ok": True,
                        "message": f"{self.player_id} disconnected.",
                    })
                    return

                else:
                    ok, message = False, f"Unknown command: {op}"

                self.client_list.send_to_client(self.client_token, {
                    "type": "command_result",
                    "ok": ok,
                    "message": message,
                    "player_id": self.player_id,
                    "state": self.data_store.get_public_state(),
                    "board": self.data_store.render_board(),
                })

                print(f"[SERVER] {self.player_id}: {message}")

        except Exception as exc:
            print(self.address, "[THREAD ERROR]:", exc)
        finally:
            if self.player_id:
                self.data_store.remove_player(self.player_id)

            self.connection.close()
            print(self.address, "[THREAD] terminated")