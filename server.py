import socket
import threading
import pickle
import sys

try:
    MAX_PLAYERS = int(sys.argv[1])
except IndexError:
    MAX_PLAYERS = 2

HOST = ""
PORT = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((HOST, PORT))
except socket.error as e:
    print(str(e))
    sys.exit()

s.listen(MAX_PLAYERS)
print(f"Server beží. Čakám na hráčov... (Max: {MAX_PLAYERS})", flush=True)

players_data = {}
connections = 0


def threaded_client(conn, player_id):
    global connections

    conn.send(pickle.dumps(player_id))

    players_data[player_id] = {"x": 100, "y": 300, "is_jumping": False, "score": 0}

    while True:
        try:
            data = pickle.loads(conn.recv(2048))

            if not data:
                break

            players_data[player_id] = data
            conn.sendall(pickle.dumps(players_data))

        except Exception:
            break

    if player_id in players_data:
        del players_data[player_id]
    connections -= 1
    conn.close()


current_player = 0

while True:
    conn, addr = s.accept()

    if connections < MAX_PLAYERS:
        threading.Thread(target=threaded_client, args=(conn, current_player)).start()
        current_player += 1
        connections += 1
    else:
        conn.close()