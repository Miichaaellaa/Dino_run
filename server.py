import pickle
import socket
import struct
import sys
import threading
import time

from game.network_config import PORT


try:
    MAX_PLAYERS = max(2, min(4, int(sys.argv[1])))
except (IndexError, ValueError):
    MAX_PLAYERS = 2

HOST = ""

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    server_socket.bind((HOST, PORT))
except socket.error as e:
    print(f"Nepodarilo sa spustit server na porte {PORT}: {e}", flush=True)
    sys.exit(1)

server_socket.listen(MAX_PLAYERS)
print(f"Server bezi. Cakam na hracov... (Max: {MAX_PLAYERS})", flush=True)

players_data = {}
connected_ids = set()
connections = 0
game_started = False
countdown = 10
countdown_active = False
global_game_over = False
global_winner = None
abort_game = False
state_lock = threading.Lock()


def recv_exact(conn, size):
    data = b""
    while len(data) < size:
        chunk = conn.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def send_packet(conn, data):
    payload = pickle.dumps(data)
    conn.sendall(struct.pack("!I", len(payload)) + payload)


def recv_packet(conn):
    header = recv_exact(conn, 4)
    if not header:
        return None
    size = struct.unpack("!I", header)[0]
    payload = recv_exact(conn, size)
    if not payload:
        return None
    return pickle.loads(payload)


def default_player_data(player_id, data):
    return {
        "name": data.get("name", f"Hrac {player_id + 1}"),
        "character": data.get("character", "deer"),
        "x": 100,
        "y": 300,
        "is_jumping": False,
        "score": 0,
        "level": 1,
        "game_speed": 5,
        "obstacles": [],
        "alive": True,
        "wants_restart": False,
    }


def manage_countdown():
    global countdown, countdown_active, game_started

    while True:
        time.sleep(1)
        with state_lock:
            if not countdown_active or game_started:
                continue

            if len(players_data) < MAX_PLAYERS:
                countdown = 10
                countdown_active = False
                continue

            countdown -= 1
            if countdown <= 0:
                game_started = True


def build_response():
    return {
        "game_started": game_started,
        "countdown": countdown,
        "players": dict(players_data),
        "total_connected": len(players_data),
        "max_players": MAX_PLAYERS,
        "global_game_over": global_game_over,
        "global_winner": global_winner,
        "abort_game": abort_game,
    }


def threaded_client(conn, player_id):
    global connections, countdown_active, game_started
    global global_game_over, global_winner, countdown, abort_game

    try:
        send_packet(conn, player_id)
    except Exception:
        with state_lock:
            connected_ids.discard(player_id)
            connections -= 1
        conn.close()
        return

    while True:
        try:
            data = recv_packet(conn)
            if not data:
                break

            with state_lock:
                message_type = data.get("type")

                if message_type == "lobby_join":
                    players_data[player_id] = default_player_data(player_id, data)

                elif message_type == "update" and player_id in players_data:
                    players_data[player_id].update(data.get("data", {}))

                elif message_type == "restart" and player_id in players_data:
                    players_data[player_id]["wants_restart"] = True
                    all_ready = all(player.get("wants_restart", False) for player in players_data.values())

                    if all_ready and players_data:
                        global_game_over = False
                        global_winner = None
                        game_started = False
                        countdown_active = True
                        countdown = 10

                        for player in players_data.values():
                            player["alive"] = True
                            player["y"] = 300
                            player["is_jumping"] = False
                            player["wants_restart"] = False

                if len(players_data) == MAX_PLAYERS and not game_started and not global_game_over:
                    countdown_active = True

                alive_players = [p_id for p_id, player in players_data.items() if player.get("alive", True)]
                if game_started and len(alive_players) <= 1:
                    global_game_over = True
                    global_winner = alive_players[0] if len(alive_players) == 1 else None

                response = build_response()

            send_packet(conn, response)

        except Exception:
            break

    with state_lock:
        players_data.pop(player_id, None)
        connected_ids.discard(player_id)
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


threading.Thread(target=manage_countdown, daemon=True).start()

while True:
    conn, _addr = server_socket.accept()

    with state_lock:
        available_ids = [player_id for player_id in range(MAX_PLAYERS) if player_id not in connected_ids]
        can_join = bool(available_ids) and not game_started

        if can_join:
            current_player = available_ids[0]
            connected_ids.add(current_player)
            connections += 1

    if can_join:
        threading.Thread(target=threaded_client, args=(conn, current_player), daemon=True).start()
    else:
        conn.close()
