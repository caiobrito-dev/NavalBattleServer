import socket
import threading

# Configurações do servidor
HOST = '0.0.0.0'
PORT = 65432

# Dicionário para armazenar informações dos jogadores
jogadores = {}

# Lock para evitar problemas de acesso concorrente
lock = threading.Lock()


def handle_client(conn, addr):
    print(f"[NOVO CLIENTE] Conectado: {addr}")
    with conn:
        # Inicializa dados do jogador
        with lock:
            jogadores[conn] = {
                'endereco': addr,
                'barcos': set(),
                'tiros': set(),
                'acertos': set(),
                'pronto': False
            }

        conn.sendall(b"Bem-vindo ao Batalha Naval!\n")

        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break

                message = data.decode().strip()
                print(f"[{addr}] {message}")

                if message.upper() == "READY":
                    with lock:
                        jogadores[conn]['pronto'] = True
                    conn.sendall(b"Voce esta pronto!\n")

                elif message.upper().startswith("BOATS"):
                    partes = message.split()
                    posicoes = set(partes[1:])
                    if len(posicoes) != 5:
                        conn.sendall(b"Erro: envie exatamente 5 posicoes.\n")
                    else:
                        with lock:
                            jogadores[conn]['barcos'] = posicoes
                        conn.sendall(b"Barcos posicionados com sucesso.\n")

                elif message.upper().startswith("ATTACK"):
                    partes = message.split()
                    if len(partes) != 2:
                        conn.sendall(b"Uso correto: ATTACK <posicao>\n")
                        continue

                    alvo = partes[1].upper()
                    acerto = False

                    with lock:
                        for player, dados in jogadores.items():
                            if player != conn:
                                if alvo in dados['barcos']:
                                    dados['barcos'].remove(alvo)
                                    dados['acertos'].add(alvo)
                                    jogadores[conn]['tiros'].add(alvo)
                                    acerto = True
                                    player.sendall(f"Seu navio na {alvo} foi atingido!\n".encode())

                    if acerto:
                        conn.sendall(f"Acertou na posicao {alvo}!\n".encode())
                    else:
                        conn.sendall(f"Errou na posicao {alvo}.\n".encode())

                elif message.upper() == "STATUS":
                    with lock:
                        barcos = jogadores[conn]['barcos']
                        tiros = jogadores[conn]['tiros']
                        acertos = jogadores[conn]['acertos']
                        status = (
                            f"STATUS:\n"
                            f"Barcos restantes: {', '.join(barcos) if barcos else 'Nenhum'}\n"
                            f"Tiros disparados: {', '.join(tiros) if tiros else 'Nenhum'}\n"
                            f"Tiros recebidos: {', '.join(acertos) if acertos else 'Nenhum'}\n"
                        )
                        conn.sendall(status.encode())

                elif message.upper() == "SAIR":
                    conn.sendall(b"Desconectando...\n")
                    break

                else:
                    conn.sendall(b"Comando desconhecido.\n")

            except Exception as e:
                print(f"Erro com {addr}: {e}")
                break

        # Remove o jogador ao desconectar
        with lock:
            if conn in jogadores:
                del jogadores[conn]

        print(f"[DESCONECTADO] {addr}")


def main():
    print("[INICIANDO] Servidor esta iniciando...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[ESPERANDO CONEXOES] Servidor escutando em {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"[ATIVO] Conexoes ativas: {threading.active_count() - 1}")


if __name__ == "__main__":
    main()
