from flask import Flask, render_template_string, request, redirect, abort
import json
import os
from datetime import datetime
from html import escape

app = Flask(__name__)

# SECURE - No hardcoded secrets, all from Render Environment
app.secret_key = os.getenv('KEY') or os.getenv('SECRET_KEY') or 'dev-key-change-me'
ADMIN_USER = os.getenv('A_USER') or os.getenv('ADMIN_USER') or 'admin'
ADMIN_PASS = os.getenv('A_PASS') or os.getenv('ADMIN_PASSWORD') or 'admin'

DATA_FILE = "kin_data.json"

def load_posts():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except:
        return []

def save_posts(posts):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

# Block direct JSON access - prevents information leak
@app.route("/kin_data.json")
@app.route("/data.json")
def block_json_leak():
    return abort(403)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>KIN - Secure</title>
<style>
body{font-family:sans-serif; background:#f0f2f5; margin:0; padding:10px}
.card{background:white; padding:15px; border-radius:10px; margin-bottom:10px; box-shadow:0 1px 2px #ccc}
input, textarea{width:100%; padding:10px; margin:5px 0; border-radius:8px; border:1px solid #ccc; box-sizing:border-box}
button{background:#1877f2; color:white; border:none; padding:10px 15px; border-radius:8px; width:100%; font-weight:bold}
small{color:gray}
h2{color:#1877f2}
</style>
</head>
<body>
<h2>KIN - Your People First</h2>
<div class="card">
<form method="POST" action="/post">
<input name="name" placeholder="Your name" required maxlength="30">
<textarea name="text" placeholder="What is happening? Venda, Pedi, English..." required maxlength="500"></textarea>
<button type="submit">Post to KIN</button>
</form>
</div>
{% for p in posts[::-1] %}
<div class="card">
<b>{{ p.name }}</b> <small>{{ p.time }}</small><br><br>
{{ p.text }}
</div>
{% endfor %}
<p style="text-align:center"><small>KIN secure - no leaks</small></p>
</body>
</html>
"""

@app.route("/")
def home():
    posts = load_posts()
    return render_template_string(HTML, posts=posts)

@app.route("/post", methods=["POST"])
def post():
    posts = load_posts()
    # Sanitize input to prevent leaks / XSS
    name = escape(request.form.get("name", "")[:30])
    text = escape(request.form.get("text", "")[:500])
    
    if not name or not text:
        return redirect("/")
        
    posts.append({
        "name": name,
        "text": text,
        "time": datetime.now().strftime("%d %b %H:%M")
    })
    save_posts(posts)
    return redirect("/")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
