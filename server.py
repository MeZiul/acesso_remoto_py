import socket
import sys

def iniciar_servidor():
    # Configurações de rede
    HOST = ''           # '' = escuta em todas as interfaces (0.0.0.0)
    PORT = 5555         # Porta arbitrária (escolha uma acima de 1024)

    # socket TCP
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Evita erro "porta já em uso" ao reiniciar rápido
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        servidor.bind((HOST, PORT))
    except socket.error as e:
        print(f"Erro ao vincular porta: {e}")
        sys.exit()

    print(f"Servidor iniciado → escutando na porta {PORT}")
    servidor.listen(1)  # Aceita apenas 1 conexão por vez

    print("Aguardando conexão do cliente...")
    conexao, endereco = servidor.accept()
    print(f"Conectado por: {endereco}")

    try:
        while True:
            comando = input("Digite o comando para enviar (ou 'sair'): ").strip()
            
            if comando.lower() == 'sair':
                break
                
            # Envia o comando
            conexao.send(comando.encode('utf-8'))
            
            # Recebe a resposta
            resposta = conexao.recv(8196).decode('utf-8', errors='ignore')
            print("\nResultado:\n" + "-"*50)
            print(resposta)
            print("-"*50 + "\n")

    except Exception as e:
        print(f"Erro na comunicação: {e}")
    
    finally:
        print("Encerrando conexão...")
        conexao.send("sair".encode('utf-8'))
        conexao.close()
        servidor.close()

if __name__ == "__main__":
    iniciar_servidor()