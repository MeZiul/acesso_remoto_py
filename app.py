from flask import Flask, render_template, session, request, jsonify
from flask_socketio import SocketIO, emit, join_room
import pyautogui
import cv2
import numpy as np
import base64
import time
import threading
from functools import wraps
import random
import string

app = Flask(__name__)
app.secret_key = "chave-super-secreta-123-mudar-isso-em-producao"

socketio = SocketIO(app, cors_allowed_origins="*")

ALLOWED_CODES = {
    "123456": {"name": "Celular Principal", "last_used": None},
    "abc123": {"name": "Notebook", "last_used": None}
}

streaming_active = False
streaming_thread = None
last_activity = time.time()
INACTIVITY_TIMEOUT = 300
active_codes = {}

def generate_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def authenticated_only(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return jsonify(success=False, error="Não autenticado"), 401
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/generate_code', methods=['POST'])
def generate_code_route():
    if 'authenticated' in session:
        return jsonify(success=False, message="sessão já ativa")
    
    code = generate_code()
    active_codes[code] = {
        "created_at": time.time(),
        "session_id": request.sid if hasattr(request, 'sid') else None
    }
    to_remove = [c for c, info in active_codes.items() if time.time() - info["created_at"] > 1800]
    for c in to_remove:
        active_codes.pop(c, None)
    return jsonify(success=True, code=code)

@app.route('/validate', methods=['POST'])
def validate():
    data = request.json
    code = data.get("code", "").strip().upper()

    if code in  active_codes:
        session['authenticated'] = True
        session['access_code'] = code
        return jsonify(success=True, message="Acesso liberado")

    if code in ALLOWED_CODES:
        session['authenticated'] = True
        session['code_used'] = code
        ALLOWED_CODES[code]["last_used"] = time.time()
        return jsonify(success=True, message="Acesso liberado")
    
    return jsonify(success=False, message="Código inválido")


@app.route('/remote')
@authenticated_only
def remote():
    return render_template("remote.html")


@socketio.on('connect')
def handle_connect():
    print("Cliente conectado:", request.sid)
    if not session.get("authenticated"):
        emit("error", {"message": "Sessão não autenticada"})
        return
    try:
        screen_width, screen_height = pyautogui.size()
        emit("screen_size", {
            "width": screen_width,
            "height": screen_height
        })
    except Exception as e:
        print("Erro ao obter screen size:", e)
        emit("screen_size", {"width": 1920, "height": 1080})


@socketio.on('disconnect')
def handle_disconnect():
    print("Cliente desconectado:", request.sid)

@socketio.on('command')
@authenticated_only
def handle_command(data):
    global last_activity
    last_activity = time.time()
    try:
        cmd_type = data.get("type")

        if cmd_type == "move":
            x, y = data.get("x"), data.get("y")
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                pyautogui.moveTo(int(x), int(y))

        elif cmd_type == "mouseDown":
            pyautogui.mouseDown()

        elif cmd_type == "mouseUp":
            pyautogui.mouseUp()
        
        elif cmd_type == "click":
            button = data.get("button", "left")
            pyautogui.click(button=button)

        elif cmd_type == "doubleClick":
            button = data.get("button", "left")
            pyautogui.doubleClick(button=button)

        elif cmd_type == "rightClick":
            x, y = data.get("x"), data.get("y")
            if x is not None and y is not None:
                pyautogui.moveTo(int(x), int(y))
            pyautogui.rightClick()

        elif cmd_type == "scroll":
            delta = data.get("deltaY", 0)
            pyautogui.scroll(int(delta))

        elif cmd_type == "key":
            key = data.get("key")
            if key and isinstance(key, str):
                pyautogui.press(key)

    except Exception as e:
        print("Erro ao executar comando:", e)


def send_screen():
    global streaming_active
    while streaming_active:
        try:
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 45]
            _, buffer = cv2.imencode('.jpg', frame, encode_param)

            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            socketio.emit('screen', jpg_as_text)
            
            socketio.sleep(0.08)  # ~12-13 fps
        except Exception as e:
            print("Erro no streaming:", e)
            socketio.sleep(1)


@socketio.on('start_stream')
@authenticated_only
def start_stream():
    global streaming_active, streaming_thread
    
    if not streaming_active:
        print("Iniciando streaming...")
        streaming_active = True
        streaming_thread = threading.Thread(target=send_screen, daemon=True)
        streaming_thread.start()
    else:
        print("Streaming já está ativo")

def monitor_inactivity():
    global streaming_active, last_activity
    while True:
        time.sleep(10)
        if streaming_active and (time.time() - last_activity > INACTIVITY_TIMEOUT):
            print("Inatividade detectada → parando streaming")
            streaming_active = False

@socketio.on('stop_stream')
@authenticated_only
def stop_stream():
    global streaming_active
    print("Parando streaming...")
    streaming_active = False


if __name__ == "__main__":
    threading.Thread(target=monitor_inactivity, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)