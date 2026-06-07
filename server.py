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
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

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
global_game_over = False
global_winner = None
abort_game = False


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
    global connections, countdown_active, game_started, global_game_over, global_winner, countdown, abort_game

    try:
        conn.send(pickle.dumps(player_id))
    except Exception:
        connections -= 1
        conn.close()
        return

    while True:
        try:
            raw_data = conn.recv(16384)
            if not raw_data:
                break

            data = pickle.loads(raw_data)

            if data.get("type") == "lobby_join":
                players_data[player_id] = {
                    "name": data["name"],
                    "character": data["character"],
                    "x": 100,
                    "y": 300,
                    "is_jumping": False,
                    "score": 0,
                    "alive": True,
                    "wants_restart": False
                }
            elif data.get("type") == "update":
                players_data[player_id].update(data["data"])
            elif data.get("type") == "restart":
                players_data[player_id]["wants_restart"] = True

                all_ready = True
                for p_id in players_data:
                    if not players_data[p_id].get("wants_restart", False):
                        all_ready = False
                        break

                if all_ready and len(players_data) > 0:
                    global_game_over = False
                    global_winner = None
                    for p_id in players_data:
                        players_data[p_id]["alive"] = True
                        players_data[p_id]["y"] = 300
                        players_data[p_id]["is_jumping"] = False
                        players_data[p_id]["wants_restart"] = False
                    game_started = False
                    countdown_active = True
                    countdown = 10

            if len(players_data) == MAX_PLAYERS and not game_started and not global_game_over:
                countdown_active = True

            alive_players = [p for p in players_data if players_data[p].get("alive", True)]
            if game_started and len(alive_players) <= 1:
                global_game_over = True
                if len(alive_players) == 1:
                    global_winner = alive_players[0]
                else:
                    global_winner = None

            response = {
                "game_started": game_started,
                "countdown": countdown,
                "players": players_data,
                "total_connected": len(players_data),
                "max_players": MAX_PLAYERS,
                "global_game_over": global_game_over,
                "global_winner": global_winner,
                "abort_game": abort_game
            }
            conn.sendall(pickle.dumps(response))

        except Exception:
            break

    if player_id in players_data:
        del players_data[player_id]

    connections -= 1

    if connections > 0 and (game_started or countdown_active or global_game_over):
        abort_game = True

    if connections == 0:
        game_started = False
        countdown_active = False
        countdown = 10
        global_game_over = False
        global_winner = None
        abort_game = False

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