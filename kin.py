import os
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import abort
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_user
from flask_login import login_required
from flask_login import current_user

app = Flask(__name__)
app.secret_key = os.getenv("KEY")

AU = os.getenv("A_USER") or "admin"
AP = os.getenv("A_PASS") or "KiN2026!"

lm = LoginManager()
lm.init_app(app)
lm.login_view = "login"

class User(UserMixin):
    def __init__(self, i, r):
        self.id = i
        self.role = r

@lm.user_loader
def load_user(uid):
    if uid == "admin":
        return User("admin","admin")
    return None

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        if u == AU and p == AP:
            login_user(User("admin","admin"))
            tgt = url_for("admin_dashboard")
            return redirect(tgt)
        return "Wrong", 403
    return render_template("login.html")

@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        abort(403)
    return render_template("admin.html")

if __name__ == "__main__":
    app.run()
