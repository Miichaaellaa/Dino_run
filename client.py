import socket
import pickle
import struct
import time

from game.network_config import PORT


def _recv_exact(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def _send_packet(sock, data):
    payload = pickle.dumps(data)
    sock.sendall(struct.pack("!I", len(payload)) + payload)


def _recv_packet(sock):
    header = _recv_exact(sock, 4)
    if not header:
        return None
    size = struct.unpack("!I", header)[0]
    payload = _recv_exact(sock, size)
    if not payload:
        return None
    return pickle.loads(payload)


class Network:
    def __init__(self, ip_adres):
        self.client = None
        self.server = ip_adres.strip()
        self.port = PORT
        self.addr = (self.server, self.port)
        self.player_id = self.connect()

    def create_socket(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(6)
        return client

    def connect(self):
        deadline = time.time() + 5
        last_error = None

        while time.time() < deadline:
            try:
                self.client = self.create_socket()
                self.client.connect(self.addr)
                return _recv_packet(self.client)
            except (socket.error, EOFError, pickle.PickleError) as e:
                last_error = e
                self.close()
                time.sleep(0.2)

        print(last_error)
        return None

    def send(self, data):
        try:
            _send_packet(self.client, data)
            return _recv_packet(self.client)
        except (socket.error, EOFError, pickle.PickleError) as e:
            print(e)
            return None

    def close(self):
        if not self.client:
            return
        try:
            self.client.close()
        except socket.error:
            pass
