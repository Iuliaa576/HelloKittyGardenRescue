import json
import threading

from server import COMMAND_SIZE


class ProcessClient(threading.Thread):
    def __init__(self, connection, address, data_store, client_list=None):
        super().__init__()
        self.connection = connection
        self.address = address
        self.data_store = data_store
        self.client_list = client_list
        self.player_id = None

    def receive_exact(self, connection, n_bytes):
        data = b''
        while len(data) < n_bytes:
            chunk = connection.recv(n_bytes - len(data))
            if not chunk:
                raise ConnectionError('Connection closed while receiving data.')
            data += chunk
        return data

    def receive_str(self, connection, n_bytes):
        data = self.receive_exact(connection, n_bytes)
        return data.decode().strip()

    def send_packet(self, payload):
        encoded = json.dumps(payload).encode()
        self.connection.sendall(len(encoded).to_bytes(4, byteorder='big') + encoded)

    def receive_packet(self):
        raw_length = self.receive_exact(self.connection, 4)
        length = int.from_bytes(raw_length, byteorder='big')
        raw_data = self.receive_exact(self.connection, length)
        return json.loads(raw_data.decode())

    def run(self):
        print(self.address, 'Thread started')
        try:
            self.player_id, player_info = self.data_store.add_player(self.address)
            self.send_packet({
                'type': 'welcome',
                'player_id': self.player_id,
                'message': f'Welcome {self.player_id}! Cooperative garden rescue started.',
                'player': player_info,
                'state': self.data_store.get_public_state(),
                'board': self.data_store.render_board(),
            })
            print(self.address, 'registered as', self.player_id)

            while True:
                op = self.receive_str(self.connection, COMMAND_SIZE)
                if op == 'move':
                    payload = self.receive_packet()
                    ok, message = self.data_store.move_player(self.player_id, payload.get('direction', '').lower())
                elif op == 'pick':
                    ok, message = self.data_store.pick_flower(self.player_id)
                elif op == 'plant':
                    ok, message = self.data_store.plant_flower(self.player_id)
                elif op == 'state':
                    ok, message = True, 'State snapshot generated.'
                elif op == 'stop':
                    self.send_packet({'type': 'bye', 'ok': True, 'message': f'{self.player_id} disconnected.'})
                    break
                else:
                    ok, message = False, f'Unknown command: {op}'

                response = {
                    'type': 'response',
                    'ok': ok,
                    'message': message,
                    'player_id': self.player_id,
                    'state': self.data_store.get_public_state(),
                    'board': self.data_store.render_board(),
                }
                self.send_packet(response)
                print(f'[SERVER] {self.player_id}: {message}')
        except (ConnectionError, OSError) as exc:
            print(self.address, 'connection closed:', exc)
        finally:
            if self.player_id:
                self.data_store.remove_player(self.player_id)
            self.connection.close()
            if self.client_list:
                self.client_list.remove_client(self.address)
            print(self.address, 'Thread terminated')
