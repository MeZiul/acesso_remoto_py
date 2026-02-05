import socket
import tkinter as tk
from tkinter import messagebox, ttk
import json
import threading
import base64
from PIL import Image, ImageTk
import io

class RemoteControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle Remoto Simples")
        self.root.geometry("1000x900")
        self.root.configure(bg="#1e1e1e")

        self.cliente_socket = None
        self.conectado = False
        self.photo = None
        self.remote_width = 1920
        self.remote_height = 1080

        self.criar_interface()

    def criar_interface(self):
        frame_topo = tk.Frame(self.root, bg="#1e1e1e")
        frame_topo.pack(fill='x', pady=12, padx=20)

        tk.Label(
            frame_topo,
            text="IP do computador remoto:",
            font=("Segoe UI", 12),
            bg="#1e1e1e",
            fg="#e0e0e0"
        ).pack(side='left', padx=(0, 10))

        self.entry_ip = tk.Entry(
            frame_topo,
            width=22,
            font=("Consolas", 13),
            bg="#2d2d2d",
            fg="#ffffff",
            insertbackground="#ffffff"
        )
        self.entry_ip.insert(0, "127.0.0.1")
        self.entry_ip.pack(side='left', padx=5)
        self.entry_ip.bind("<Return>", lambda e: self.conectar())

        tk.Button(frame_topo, text="Conectar", command=self.conectar, bg="#4CAF50", fg="white", font=("Segoe UI", 11, "bold"), width=12, relief="flat").pack(side='left', padx=10)
        tk.Button(frame_topo, text="Desconectar", command=self.desconectar, bg="#f44336", fg="white", font=("Segoe UI", 11, "bold"), width=12, relief="flat").pack(side='left')

        # Área de controle (tela remota simulada)
        self.canvas = tk.Canvas(
            self.root,
            bg="#0a0a0a",
            width=960,
            height=540,
            highlightthickness=1,
            highlightbackground="#444"
        )
        self.canvas.pack(pady=15, padx=10)

        # Eventos de mouse
        self.canvas.bind("<Motion>", self.mouse_move)
        self.canvas.bind("<Button-1>", self.clique_esquerdo)
        self.canvas.bind("<Button-3>", self.clique_direito)
        self.canvas.bind("<Double-Button-1>", self.duplo_clique)

        # ── Campo para digitar texto + Enter para enviar ──────────────
        frame_teclado = tk.Frame(self.root, bg="#1e1e1e")
        frame_teclado.pack(fill='x', padx=20, pady=8)

        tk.Label(frame_teclado, text="Digitar no remoto:", font=("Segoe UI", 11), bg="#1e1e1e", fg="#cccccc").pack(side='left', padx=(0,10))

        self.entry_texto = tk.Entry(frame_teclado, font=("Consolas", 12), width=50, bg="#2d2d2d", fg="#ffffff", insertbackground="#ffffff")
        self.entry_texto.pack(side='left', fill='x', expand=True, padx=5)
        self.entry_texto.bind("<Return>", self.enviar_texto)

        tk.Button(frame_teclado, text="Enviar", command=self.enviar_texto, bg="#2196F3", fg="white", width=10).pack(side='left', padx=5)

        # ── Botões de atalhos comuns ──────────────────────────────────
        frame_atalhos = tk.Frame(self.root, bg="#1e1e1e")
        frame_atalhos.pack(pady=8)

        atalhos = [
            ("Ctrl+C", ["ctrl", "c"]),
            ("Ctrl+V", ["ctrl", "v"]),
            ("Ctrl+Z", ["ctrl", "z"]),
            ("Alt+Tab", ["alt", "tab"]),
            ("Enter", "enter"),
            ("Esc", "esc"),
            ("Backspace", "backspace"),
        ]

        for texto, teclas in atalhos:
            if isinstance(teclas, list):
                cmd = lambda t=teclas: self.enviar_hotkey(t)
            else:
                cmd = lambda t=teclas: self.enviar_tecla(t)

            tk.Button(frame_atalhos, text=texto, command=cmd, bg="#444", fg="white", width=10, font=("Segoe UI", 10)).pack(side='left', padx=6)

        # Área de status
        self.label_status = tk.Label(
            self.root,
            text="Desconectado",
            fg="#ff5555",
            bg="#1e1e1e",
            font=("Segoe UI", 12)
        )
        self.label_status.pack(pady=5)

        # Coordenadas do mouse
        self.label_coords = tk.Label(
            self.root,
            text="X: 0   Y: 0",
            fg="#aaaaaa",
            bg="#1e1e1e",
            font=("Consolas", 11)
        )
        self.label_coords.pack()

        # Botões de scroll
        frame_scroll = tk.Frame(self.root, bg="#1e1e1e")
        frame_scroll.pack(pady=8)

        tk.Button(
            frame_scroll,
            text="Scroll ↑",
            command=lambda: self.enviar_scroll(300),
            bg="#555555",
            fg="white",
            font=("Segoe UI", 10),
            width=12
        ).pack(side='left', padx=8)

        tk.Button(
            frame_scroll,
            text="Scroll ↓",
            command=lambda: self.enviar_scroll(-300),
            bg="#555555",
            fg="white",
            font=("Segoe UI", 10),
            width=12
        ).pack(side='left', padx=8)

    def conectar(self):
        if self.conectado:
            messagebox.showinfo("Aviso", "Já está conectado.")
            return

        ip = self.entry_ip.get().strip()
        if not ip:
            messagebox.showwarning("Atenção", "Digite o endereço IP.")
            return

        try:
            self.cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.cliente_socket.connect((ip, 5555))
            self.conectado = True
            self.label_status.config(text=f"Conectado → {ip}", fg="#55ff55")

            self.thread_receber = threading.Thread(target=self.receber_mensagens, daemon=True)
            self.thread_receber.start()

        except Exception as e:
            messagebox.showerror("Erro de conexão", f"Não foi possível conectar.\n\n{str(e)}")

    def desconectar(self):
        if self.conectado:
            try:
                self.cliente_socket.send("sair".encode())
                self.cliente_socket.close()
            except:
                pass
            self.conectado = False
            self.label_status.config(text="Desconectado", fg="#ff5555")
            self.canvas.delete("all")

    def enviar_comando(self, comando_dict):
        if not self.conectado:
            return
        try:
            msg = json.dumps(comando_dict) + "\n"
            self.cliente_socket.send(msg.encode())
        except Exception as e:
            print("Erro ao enviar comando:", e)
            self.desconectar()
    
    def enviar_texto(self, event=None):
        texto = self.entry_texto.get()
        if texto:
            self.enviar_comando({"type": "type", "text": texto})
            self.entry_texto.delete(0, tk.END)

    def enviar_tecla(self, tecla):
        self.enviar_comando({"type": "key_press", "key": tecla})

    def enviar_hotkey(self, teclas):
        self.enviar_comando({"type": "hotkey", "keys": teclas})

    def mouse_move(self, event):
        # Ajuste conforme a resolução real do PC remoto (exemplo 1920×1080)
        x_remoto = int(event.x * (1920 / 960))
        y_remoto = int(event.y * (1080 / 540))

        self.label_coords.config(text=f"X: {x_remoto:4d}   Y: {y_remoto:4d}")
        self.enviar_comando({"type": "mouse_move", "x": x_remoto, "y": y_remoto})

    def clique_esquerdo(self, event):
        self.enviar_comando({"type": "click"})

    def clique_direito(self, event):
        self.enviar_comando({"type": "right_click"})

    def duplo_clique(self, event):
        self.enviar_comando({"type": "double_click"})

    def enviar_scroll(self, quantidade):
        self.enviar_comando({"type": "scroll", "amount": quantidade})

    def receber_mensagens(self):
        buffer = ""
        while self.conectado:
            try:
                dados = self.cliente_socket.recv(65536).decode(errors='ignore')
                if not dados:
                    break
                buffer += dados
                while "\n" in buffer:
                    linha, buffer = buffer.split("\n", 1)
                    if not linha.strip():
                        continue
                    
                    try:
                        msg = json.loads(linha)

                        if msg["type"] == "screen_info":
                            self.remote_width = msg["width"]
                            self.remote_height = msg["height"]
                            print(f"Resolução remota: {self.remote_width}x{self.remote_height}")

                        elif msg["type"] == "screen":
                            img_data = base64.b64decode(msg["data"])
                            img = Image.open(io.BytesIO(img_data))
                            
                            img = img.resize((960, 540), Image.LANCZOS)
                            self.photo = ImageTk.PhotoImage(img)
                            self.canvas.delete("all")
                            self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
                        
                    except Exception as e:
                        print("Erro ao processar mensagem:", e)

            except Exception as e:
                print("Erro na recepção de dados:", e)
                break

        self.desconectar()

    def on_closing(self):
        self.desconectar()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteControlApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()