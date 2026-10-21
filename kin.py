import json
import os
from flask import Flask, render_template_string, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'kin-secret-2026')
db_url = os.environ.get('DATABASE_URL', 'sqlite:///kin.db')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

SA = [
    ("Venda","ven"), ("Sepedi","nso"), ("Tsonga","tso"),
    ("Zulu","zul"), ("Xhosa","xho"), ("Tswana","tsn"),
    ("Sotho","sot"), ("Swati","ssw"), ("Ndebele","nbl"),
    ("Afrikaans","afr"), ("English","eng")
]

try:
    L = json.load(open("languages_8324.json"))
except:
    L = [{"name": n, "iso_639_3": c} for n,c in SA]

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_number = db.Column(db.String(13), unique=True, nullable=False)
    username = db.Column(db.String(80))
    password_hash = db.Column(db.String(200))
    role = db.Column(db.String(20), default='user')
    language = db.Column(db.String(50))
    def set_password(self, p): self.password_hash = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.password_hash, p)

@login_manager.user_loader
def load_user(uid): return User.query.get(int(uid))

LOGIN_HTML = """
<h2>KiN - We are in South Africa</h2>
<p>Sign in with ID - 8324 langs - Venda Sepedi Tsonga</p>
<form method="POST">
ID (13 digits): <input name="id_number" required maxlength="13"><br>
Password: <input type="password" name="password" required><br>
<button>Sign In</button>
</form>
<p style="color:red">{{msg}}</p>
"""

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect('/admin-dashboard' if current_user.role=='admin' else '/user-dashboard')
    return redirect('/login')

@app.route('/login', methods=['GET','POST'])
def login():
    msg=""
    if request.method=='POST':
        idn=request.form.get('id_number','').strip()
        pwd=request.form.get('password','')
        if len(idn)!=13 or not idn.isdigit():
            msg="ID must be 13 digits"
        else:
            u=User.query.filter_by(id_number=idn).first()
            if u and u.check_password(pwd):
                login_user(u)
                return redirect('/admin-dashboard' if u.role=='admin' else '/user-dashboard')
            msg="Invalid ID or password"
    return render_template_string(LOGIN_HTML, msg=msg)

@app.route('/user-dashboard')
@login_required
def user_dash():
    return f"<h2>User Dashboard</h2>Welcome {current_user.id_number}<br>Lang: {current_user.language}<br>Role: {current_user.role}<br><p>You can only view your own account - cannot change others</p><a href='/logout'>Logout</a>"

@app.route('/admin-dashboard')
@login_required
def admin_dash():
    if current_user.role!='admin': return "Access denied - Admin only",403
    users=User.query.all()
    html=f"<h2>Admin Dashboard - {len(L)} langs</h2><p>SA Langs: {SA}</p><h3>Users:</h3>"
    for u in users: html+=f"{u.id_number} - {u.role} - {u.language}<br>"
    html+="<br><a href='/logout'>Logout</a>"
    return html

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

with app.app_context():
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        a=User(id_number='0000000000000', username='admin', role='admin', language='Admin')
        a.set_password(os.environ.get('ADMIN_PASS','Kin@2026!Secure'))
        db.session.add(a)
        db.session.commit()
