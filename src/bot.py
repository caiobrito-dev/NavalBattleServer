import socket
import time
import string

HOST = '127.0.0.1'  # IP do servidor
PORT = 65432        # Porta do servidor

# Gera coordenadas A1 até J10
def gerar_coordenadas():
    letras = string.ascii_uppercase[:10]
    return [f"{l}{n}" for l in letras for n in range(1, 11)]

# Envia mensagem com encoding e espera resposta
def enviar_e_receber(sock, msg):
    sock.sendall(msg.encode())
    data = sock.recv(2048).decode()
    print(f"[Servidor]: {data.strip()}")
    return data

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print("[Bot] Conectado ao servidor")

        # Recebe mensagem de boas-vindas
        print(s.recv(1024).decode())

        time.sleep(1)

        # Sinaliza que está pronto
        enviar_e_receber(s, "READY")
        time.sleep(1)

        # Posiciona 3 barcos
        barcos = [
            ("3", "A1", "A3"),
            ("2", "B1", "B2"),
            ("4", "C1", "C4"),
        ]

        for barco in barcos:
            comando = f"BOATS {barco[0]} {barco[1]} {barco[2]}"
            enviar_e_receber(s, comando)
            time.sleep(1)

        # Começa a atacar
        posicoes = gerar_coordenadas()
        index = 0

        while True:
            try:
                # Espera o servidor enviar algo antes de atacar
                resposta = s.recv(2048).decode()
                print(f"[Servidor]: {resposta.strip()}")

                if "PARABENS" in resposta.upper() or "DESCONECTANDO" in resposta.upper():
                    print("[Bot] Fim de jogo.")
                    break

                if "ERROU" in resposta.upper() or "ACERTOU" in resposta.upper() or "Voce esta pronto" in resposta:
                    # Espera uma resposta antes de atacar novamente
                    if index < len(posicoes):
                        ataque = posicoes[index]
                        print(f"[Bot] Atacando {ataque}")
                        s.sendall(f"ATTACK {ataque}".encode())
                        index += 1
                        time.sleep(1)

            except Exception as e:
                print(f"[ERRO] {e}")
                break

if __name__ == "__main__":
    main()
