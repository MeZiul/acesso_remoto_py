from flask import Flask, request, render_template_string
import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Controle Remoto</title>
<style>
body { font-family: Arial; text-align: center; background: #111; color: #fff; }
button { font-size: 20px; margin: 10px; padding: 20px; width: 80%; }
</style>
</head>
<body>
<h2>Controle Remoto</h2>

<button onclick="send('click')">Clique</button>
<button onclick="send('right_click')">Clique Direito</button>
<button onclick="send('double_click')">Duplo Clique</button>
<button onclick="send('scroll_up')">Scroll ↑</button>
<button onclick="send('scroll_down')">Scroll ↓</button>

<script>
function send(cmd) {
    fetch('/cmd', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({type: cmd})
    });
}
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/cmd', methods=['POST'])
def cmd():
    data = request.json
    t = data.get('type')

    if t == 'click':
        pyautogui.click()
    elif t == 'right_click':
        pyautogui.rightClick()
    elif t == 'double_click':
        pyautogui.doubleClick()
    elif t == 'scroll_up':
        pyautogui.scroll(300)
    elif t == 'scroll_down':
        pyautogui.scroll(-300)

    return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
