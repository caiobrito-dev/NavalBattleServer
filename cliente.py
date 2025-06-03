import socket as sk
import threading

host = "127.0.0.1" 
port = 65432

def receiveMessage(sock): 
    while True:
        try: 
            data = sock.recv(1024)
            if not data: 
                print("Disconnected from server")
                break
            print(f"Server: {data.decode().strip()}")   
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def main(): 
    with sk.socket(sk.AF_INET, sk.SOCK_STREAM) as sock:
        try:
            sock.connect((host, port))
            print(f"Conectado ao servidor {host}:{port}")
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            return

        # Thread para ouvir mensagens do servidor
        thread = threading.Thread(target=receiveMessage, args=(sock,))
        thread.daemon = True
        thread.start()

        print("\n>>> Comandos disponíveis:")
        print("READY               → Para sinalizar que está pronto")
        print("ATTACK <posicao>    → Para atacar (ex: ATTACK A1)")
        print("SAIR                → Para desconectar\n")

        while True:
            message = input("> ")

            if message.upper() == 'SAIR':
                print("Desconectando...")
                break

            if message.strip() == '':
                continue

            try:
                sock.sendall(f"{message}\n".encode())
            except:
                print("Erro ao enviar mensagem. Encerrando.")
                break

if __name__ == "__main__":
    main()