import json
import socket

from client import COMMAND_SIZE, SERVER_ADDRESS, PORT, BROADCAST_PORT
from client.broadcast_receiver import BroadcastReceiver


def receive_exact(connection, n_bytes):
    data = b''
    while len(data) < n_bytes:
        chunk = connection.recv(n_bytes - len(data))
        if not chunk:
            raise ConnectionError('Connection closed while receiving data.')
        data += chunk
    return data


def send_str(connection, value):
    connection.sendall(value.ljust(COMMAND_SIZE).encode())


def send_packet(connection, payload):
    encoded = json.dumps(payload).encode()
    connection.sendall(len(encoded).to_bytes(4, byteorder='big') + encoded)


def receive_packet(connection):
    raw_length = receive_exact(connection, 4)
    length = int.from_bytes(raw_length, byteorder='big')
    raw_data = receive_exact(connection, length)
    return json.loads(raw_data.decode())


class Interaction:
    def _print_help(self):
        print('Commands:')
        print('  move up|down|left|right')
        print('  pick')
        print('  plant')
        print('  state')
        print('  stop')

    def _print_response(self, response):
        print('\n--- Server response ---')
        print(response.get('message'))
        if response.get('board'):
            print(response['board'])
        state = response.get('state', {})
        player_id = response.get('player_id')
        if player_id and player_id in state.get('players', {}):
            player = state['players'][player_id]
            print('Your position:', tuple(player['position']))
            print('Carrying flower:', player['has_flower'])
        print('Time remaining:', state.get('time_remaining_seconds'))
        print('Winner:', state.get('winner'))
        print('-----------------------\n')

    def execute(self):
        connection = socket.socket()
        connection.connect((SERVER_ADDRESS, PORT))

        broadcast_conn = socket.socket()
        broadcast_conn.connect((SERVER_ADDRESS, BROADCAST_PORT))
        receiver = BroadcastReceiver(broadcast_conn)
        receiver.start()

        welcome = receive_packet(connection)
        print(welcome.get('message'))
        print('Assigned player id:', welcome.get('player_id'))
        print(welcome.get('board', ''))
        self._print_help()

        try:
            while True:
                raw = input('Command: ').strip().lower()
                if not raw:
                    continue
                parts = raw.split()
                command = parts[0]

                if command == 'move':
                    if len(parts) != 2:
                        print('Usage: move up|down|left|right')
                        continue
                    send_str(connection, 'move')
                    send_packet(connection, {'direction': parts[1]})
                elif command in ('pick', 'plant', 'state', 'stop'):
                    send_str(connection, command)
                    if command == 'stop':
                        bye = receive_packet(connection)
                        print(bye.get('message'))
                        break
                elif command == 'help':
                    self._print_help()
                    continue
                else:
                    print('Unknown command. Type help for the list.')
                    continue

                response = receive_packet(connection)
                self._print_response(response)
        finally:
            connection.close()
            broadcast_conn.close()
