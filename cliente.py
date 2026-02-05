import socket
import json
import pyautogui
import threading
import time
import base64
from PIL import ImageGrab, Image
import io

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.04

CAPTURE_INTERVAL = 0.7
QUALITY = 50

def conectar_ao_controlador():
    HOST = '10.10.100.176'   # ← Mudar para o IP real do controlador quando for testar em outra máquina
    PORT = 5555

    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        cliente.connect((HOST, PORT))
        print("Conectado ao controlador com sucesso!")
    except Exception as e:
        print(f"Erro ao conectar: {e}")
        return
    
    largura, altura = pyautogui.size()
    info_inicial = json.dumps({
        "type": "screen_info",
        "width": largura,
        "height": altura
    }) + "\n"
    cliente.send(info_inicial.encode())

    thread_captura = threading.Thread(target=enviar_tela_continua, args=(cliente,), daemon=True)
    thread_captura.start()

    while True:
        try:
            # Recebe comando do controlador
            dados = cliente.recv(8192).decode('utf-8', errors='ignore').strip()
            
            if not dados or dados.lower() == 'sair':
                print("Comando de saída recebido. Encerrando...")
                break

            try:
                comando = json.loads(dados)
                tipo = comando.get('type')
                
                if tipo == 'mouse_move':
                    x = comando['x']
                    y = comando['y']
                    pyautogui.moveTo(x,y,duration=0.1)
                    cliente.send("OK".encode())

                elif tipo == "click":
                    pyautogui.click()
                    cliente.send("OK".encode())
                    
                elif tipo == "right_click":
                    pyautogui.rightClick()
                    cliente.send("OK".encode())

                elif tipo == "double_click":
                    pyautogui.doubleClick()
                    cliente.send("OK".encode())

                elif tipo == "scroll":
                    pyautogui.scroll(comando['amount'])
                    cliente.send("OK".encode())
                
                elif tipo == 'type':
                    texto = comando.get('text', '')
                    pyautogui.write(texto, interval=0.03)
                    cliente.send("OK\n".encode())

                elif tipo == 'key_press':
                    tecla = comando.get('key')
                    pyautogui.press(tecla)
                    cliente.send("OK\n".encode())

                elif tipo == 'key_down':
                    tecla = comando.get('key')
                    pyautogui.keyDown(tecla)
                    cliente.send("OK\n".encode())

                elif tipo == 'key_up':
                    tecla = comando.get('key')
                    pyautogui.keyUp(tecla)
                    cliente.send("OK\n".encode())

                elif tipo == 'hotkey':
                    teclas = comando.get('keys', [])
                    if teclas:
                        pyautogui.hotkey(*teclas)
                    cliente.send("OK\n".encode())

            except json.JSONDecodeError:
                pass

        except Exception as e:
            print(f"Erro na comunicação: {e}")
            break
        
    cliente.close()
    print("Conexão encerrada.")

def enviar_tela_continua(sock):
    while True:
        try:
            screenshot = ImageGrab.grab()
            
            buffer = io.BytesIO()
            screenshot.save(buffer, format="JPEG", quality=QUALITY, optimize=True)
            img_bytes = buffer.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            mensagem = json.dumps({
                "type": "screen",
                "data": img_base64
            }) + "\n"

            sock.send(mensagem.encode('utf-8'))

            time.sleep(CAPTURE_INTERVAL)

        except Exception as e:
            print(f"Erro ao enviar tela: {e}")
            time.sleep(2)

if __name__ == "__main__":
    conectar_ao_controlador()
