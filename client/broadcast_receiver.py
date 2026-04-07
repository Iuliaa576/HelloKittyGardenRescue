import json
import threading


class BroadcastReceiver(threading.Thread):
    def __init__(self, connection):
        super().__init__(daemon=True)
        self.connection = connection

    def receive_exact(self, n_bytes):
        data = b''
        while len(data) < n_bytes:
            chunk = self.connection.recv(n_bytes - len(data))
            if not chunk:
                raise ConnectionError('Connection closed while receiving broadcast data.')
            data += chunk
        return data

    def receive_data(self):
        raw_length = self.receive_exact(4)
        length = int.from_bytes(raw_length, byteorder='big')
        raw_data = self.receive_exact(length)
        return json.loads(raw_data.decode())

    def run(self):
        while True:
            try:
                data = self.receive_data()
                print('\n=== Broadcast game state update ===')
                print(data.get('board', ''))
                state = data.get('state', {})
                print('Time remaining:', state.get('time_remaining_seconds'))
                print('Winner:', state.get('winner'))
                events = state.get('recent_events', [])
                if events:
                    print('Recent events:')
                    for event in events[-3:]:
                        print(f"  t={event['timestamp']}: {event['message']}")
                print('===================================\n')
            except (ConnectionError, OSError):
                print('Broadcast connection closed.')
                break
