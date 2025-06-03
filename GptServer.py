import socket
import threading

HOST = '0.0.0.0'
PORT = 65432

players = []
lock = threading.Lock()
game_started = False
current_turn = 0

# Tabuleiros dos jogadores
boards = [set(["A1", "B2", "C3"]), set(["D4", "E5", "F6"])]
hits = [set(), set()]

def handle_client(conn, player_id):
    global current_turn, game_started
    conn.sendall(b'CONNECTED\n')

    while True:
        try:
            data = conn.recv(1024)
            if not data:
                print(f'Player {player_id} disconnected.')
                break

            message = data.decode().strip()
            print(f"Player {player_id} says: {message}")

            if message == "READY":
                with lock:
                    if len(players) == 2 and not game_started:
                        game_started = True
                        broadcast("START")
                        players[current_turn].sendall(b'YOUR_TURN\n')
                    else:
                        conn.sendall(b'WAITING\n')

            elif message.startswith("ATTACK"):
                with lock:
                    if current_turn != player_id:
                        conn.sendall(b'WAIT\n')
                        continue

                    _, pos = message.split()
                    opponent = 1 - player_id

                    if pos in boards[opponent]:
                        hits[player_id].add(pos)
                        boards[opponent].remove(pos)
                        if len(boards[opponent]) == 0:
                            conn.sendall(b'YOU_WIN\n')
                            players[opponent].sendall(b'YOU_LOSE\n')
                            broadcast('GAME_OVER')
                            continue
                        conn.sendall(b'HIT\n')
                        players[opponent].sendall(f'OPPONENT_HIT {pos}\n'.encode())
                    else:
                        conn.sendall(b'MISS\n')
                        players[opponent].sendall(f'OPPONENT_MISS {pos}\n'.encode())

                    current_turn = opponent
                    players[current_turn].sendall(b'YOUR_TURN\n')

            else:
                conn.sendall(b'ERROR Unknown Command\n')

        except Exception as e:
            print(f'Error with player {player_id}: {e}')
            break

    conn.close()

def broadcast(message):
    for p in players:
        p.sendall(f'{message}\n'.encode())

def start_server():
    global players

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Servidor rodando em {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        with lock:
            if len(players) >= 2:
                conn.sendall(b'FULL\n')
                conn.close()
                continue
            player_id = len(players)
            players.append(conn)
            print(f"Player {player_id} conectado: {addr}")
            conn.sendall(f'PLAYER {player_id}\n'.encode())

            thread = threading.Thread(target=handle_client, args=(conn, player_id))
            thread.start()

start_server()
