import socket
import threading
import pickle
import sys
import time

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
game_started = False
countdown = 10
countdown_active = False

def manage_countdown():
    global countdown, game_started, countdown_active
    while True:
        time.sleep(1)
        if countdown_active and not game_started:
            if len(players_data) < MAX_PLAYERS:
                countdown = 10
                countdown_active = False
            else:
                countdown -= 1
                if countdown <= 0:
                    game_started = True

threading.Thread(target=manage_countdown, daemon=True).start()

def threaded_client(conn, player_id):
    global connections, countdown_active

    conn.send(pickle.dumps(player_id))

    while True:
        try:
            data = pickle.loads(conn.recv(2048))
            if not data:
                break

            if data.get("type") == "lobby_join":
                players_data[player_id] = {
                    "name": data["name"],
                    "character": data["character"],
                    "x": 100,
                    "y": 300,
                    "is_jumping": False,
                    "score": 0
                }
            elif data.get("type") == "update":
                players_data[player_id].update(data["data"])

            if len(players_data) == MAX_PLAYERS and not game_started:
                countdown_active = True

            response = {
                "game_started": game_started,
                "countdown": countdown,
                "players": players_data,
                "total_connected": len(players_data),
                "max_players": MAX_PLAYERS
            }
            conn.sendall(pickle.dumps(response))
        except Exception:
            break

    if player_id in players_data:
        del players_data[player_id]
    connections -= 1
    conn.close()

current_player = 0
while True:
    conn, addr = s.accept()
    if connections < MAX_PLAYERS and not game_started:
        threading.Thread(target=threaded_client, args=(conn, current_player)).start()
        current_player += 1
        connections += 1
    else:
        conn.close()