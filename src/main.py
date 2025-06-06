import socket
import threading

# Configurações do servidor
HOST = '0.0.0.0'
PORT = 65432

# Dicionário para armazenar informações dos jogadores
jogadores = {}

# Lock para evitar problemas de acesso concorrente
lock = threading.Lock()

def gerar_posicoes(inicio, fim): # A1 E1 5posições
    linha_inicio = inicio[0].upper()
    coluna_inicio = int(inicio[1:])
    linha_fim = fim[0].upper()
    coluna_fim = int(fim[1:])

    posicoes = []

    if linha_inicio == linha_fim:  # Mesma linha, percorre colunas
        for c in range(min(coluna_inicio, coluna_fim), max(coluna_inicio, coluna_fim) + 1):
            posicoes.append(f"{linha_inicio}{c}")

    elif coluna_inicio == coluna_fim:  # Mesma coluna, percorre linhas
        for l in range(ord(linha_inicio), ord(linha_fim) + 1):
            posicoes.append(f"{chr(l)}{coluna_inicio}")

    else:
        posicoes = []  # Barcos na diagonal são inválidos

    return posicoes


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
                    partes = message.split()
                    if len(partes) != 4:
                        conn.sendall(b"Uso correto: BOATS <tamanho> <inicio> <fim>\n")
                        continue

                    tamanho = int(partes[1])
                    inicio = partes[2].upper()
                    fim = partes[3].upper()

                    posicoes = gerar_posicoes(inicio, fim)

                    if not posicoes:
                        conn.sendall(b"Erro: barco em posicao invalida (somente linha ou coluna)\n")
                        continue

                    if len(posicoes) != tamanho:
                        conn.sendall(b"Erro: tamanho informado nao bate com a quantidade de posicoes\n")
                        continue

                    with lock:
                        barco = {
                            "tamanho": tamanho,
                            "inicio": inicio,
                            "fim": fim,
                            "posicoes": posicoes.copy()
                        }
                        jogadores[conn]['barcos'].append(barco)
                        conn.sendall(f"Barco adicionado nas posicoes {posicoes}\n".encode())



                # Comando para atacar um barco do oponente
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
                                barcos_atingidos = []

                                for barco in dados['barcos']:
                                    if alvo in barco['posicoes']:
                                        barco['posicoes'].remove(alvo)
                                        jogadores[conn]['acertos'].append(alvo)
                                        jogadores[conn]['tiros'].append(alvo)
                                        acerto = True

                                        if not barco['posicoes']:
                                            barcos_atingidos.append(barco)

                                for b in barcos_atingidos:
                                    dados['barcos'].remove(b)

                    if acerto:
                        conn.sendall(f"ACERTOU {alvo}\n".encode())

                        # Verifica se venceu
                        with lock:
                            inimigos_restantes = [
                                dados for player, dados in jogadores.items() if player != conn and dados['barcos']
                            ]
                            if not inimigos_restantes:
                                conn.sendall(b"PARABENS! VOCE VENCEU!\n")
                                break

                    else:
                        conn.sendall(f"ERROU {alvo}\n".encode())

                # Função para retornar dados de um player em especifico 
                elif message.upper() == "STATUS":
                    with lock:
                        barcos = jogadores[conn]['barcos']
                        acertos = jogadores[conn]['acertos']
                        status = (
                            f"STATUS:\n"
                            f"Barcos restantes: {', '.join([str(barco) for barco in barcos]) if barcos else 'Nenhum'}\n"
                            f"{jogadores.items}"
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
