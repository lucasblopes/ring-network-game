import socket
from settings import BUFFER_SIZE, HOSTS, PORTS, NUM_PLAYERS


class Network:
    def __init__(self, player_id):
        self.player_id = player_id
        self.host = HOSTS[player_id]
        self.port = PORTS[player_id]
        self.prev_host = HOSTS[(player_id - 1) % NUM_PLAYERS]
        self.prev_port = PORTS[(player_id - 1) % NUM_PLAYERS]
        self.next_host = HOSTS[(player_id + 1) % NUM_PLAYERS]
        self.next_port = PORTS[(player_id + 1) % NUM_PLAYERS]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind((self.host, self.port))
        self.baton = player_id == 0

    def send(self, source, destination, action, data):
        message = f"{source}|{destination}|{action}|{data}"
        #print("Sent " + message)
        # input(message)
        self.sock.sendto(message.encode("utf-8"), (self.next_host, self.next_port))

    def receive(self):
        data, addr = self.sock.recvfrom(BUFFER_SIZE)
        if addr == (self.prev_host, self.prev_port):
            message = data.decode("utf-8")
            # input(message)
            # print("Received " + message)
            return self.parse_message(message)
        else:
            return None

    def parse_message(self, message):
        parts = message.split("|")
        return {
            "source": int(parts[0]),
            "destination": int(parts[1]),
            "action": int(parts[2]),
            "data": parts[3],
        }

    def receive_baton(self):
        self.baton = True

    def drop_baton(self):
        self.baton = False
