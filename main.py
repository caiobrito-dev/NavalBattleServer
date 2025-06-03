import socket as sk 
import threading

host = "0.0.0.0"
port = 65432

players = []
lock = threading.Lock()
gameStarted = False
currentTurn = 0

boards = [set(), set()]
hits = [set(), set()]

def handleClient(conn, playerID): 
    global currentTurn, gameStarted
    conn.sendall(b"Connected\n")

    buffer = ""

    while True: 
        try: 
            data = conn.recv(1024)
            if not data:
                print(f"Player {playerID} disconnected")
                break

            buffer += data.decode()


            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                message = line.strip()
                
                print(f"Player {playerID} says: {message}")

                conn.sendall(f"Server received: {message}\n".encode())
        
        except Exception as e:
            print(f"Error with player {playerID}: {e}")
            break

    conn.close()

def startServer(): 
    global players

    playerID = 0
    
    server = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
    server.bind((host, port))
    server.listen()

    print(f"Servidor rodando em {host}, {port}")

    while True:
        conn, addr = server.accept()

        with lock:
            players.append(conn)

        thread = threading.Thread(target = handleClient, args=(conn, playerID))
        thread.start()
        playerID += 1


startServer()