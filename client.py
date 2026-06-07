import socket
import pickle

class Network:
    def __init__(self, ip_adres):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = ip_adres
        self.port = 5555
        self.addr = (self.server, self.port)
        self.player_id = self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            return pickle.loads(self.client.recv(16384))
        except socket.error as e:
            print(e)
            return None

    def send(self, data):
        try:
            self.client.send(pickle.dumps(data))
            return pickle.loads(self.client.recv(16384))
        except socket.error as e:
            print(e)
            return None