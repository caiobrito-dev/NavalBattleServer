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
        
            # Objeto do cliente é adicionado ao dicionário de jogadores
            jogadores[conn] = {
                'endereco': addr,
                'barcos': [],
                'tiros': [],
                'acertos': [],
                'pronto': False
            }

        conn.sendall(b"Bem-vindo ao Batalha Naval!\n")


        # Loop principal onde o servidor recebe todos os comandos do cliente
        while True:
            try:

                # Recebe dados do cliente
                data = conn.recv(1024)
                if not data:
                    break

                message = data.decode().strip()
                print(f"[{addr}] {message}")


                # Mensagem de inicio do jogo, somente dps dessa mensagem o jogador pode enviar certos comandos
                if message.upper() == "READY":
                    with lock:
                        jogadores[conn]['pronto'] = True
                    conn.sendall(b"Voce esta pronto!\n")

                # Comando para posicionar barcos 
                elif message.upper().startswith("BOATS"):

                    # Exemplo de chegada: "3 A3 A6"
                    # 3 = Tamanho do barco, A3 = Posição inicial, A6 = Posição final

                    partes = message.split()
                    posicoes = set(partes[1:])
                    if len(posicoes) != 3:
                        conn.sendall(b"Erro: envie exatamente 3 informacoes.\n")

                    else:
                        with lock:
                            barco = {
                                "tamanho": partes[1], 
                                "inicio": partes[2], 
                                "fim": partes[3]
                                }
                            jogadores[conn]['barcos'].append(barco) 

                        conn.sendall(b"Barcos posicionados com sucesso.\n")


                # Comando para atacar um barco do oponente
                elif message.upper().startswith("ATTACK"):
                    partes = message.split()

                    # Confirma se está passando duas coordenadas para o ataque 
                    if len(partes) != 2:
                        conn.sendall(b"Uso correto: ATTACK <posicao>\n")
                        continue

                    # Formato do alvo: A3, B5, etc.
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
                        conn.sendall(f"ACERTOU {alvo}".encode())
                    else:
                        conn.sendall(f"ERROU {alvo}.\n".encode())

                # Função para retornar dados de um player em especifico 
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

    # Inicio do servidor 
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[ESPERANDO CONEXOES] Servidor escutando em {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            # Cria uma nova thread para cada cliente conectado
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print(f"[ATIVO] Conexoes ativas: {threading.active_count() - 1}")


if __name__ == "__main__":
    main()
