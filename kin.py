import json
import os
from flask import Flask, render_template, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'kin-secret-2026')
db_url = os.environ.get('DATABASE_URL', 'sqlite:///kin.db')
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def load_langs():
    try:
        with open('languages_8324.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        try:
            with open('kin/languages_8324.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

L = load_langs()

@app.route('/')
def home():
    return render_template('home.html', langs=L, total=len(L) if isinstance(L, (list, dict)) else 8324)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dash'))
            return redirect(url_for('dashboard'))
        return render_template_string("<h3>Invalid login</h3><a href='/login'>Back</a>")
    return render_template_string("""
    <form method='post' style='max-width:300px;margin:50px auto'>
    <h2>Login</h2>
    <input name='username' placeholder='username' style='width:100%;padding:8px;margin:5px 0'><br>
    <input name='password' type='password' placeholder='password' style='width:100%;padding:8px;margin:5px 0'><br>
    <button style='width:100%;padding:10px;background:#22c55e;color:white;border:none'>Login</button>
    </form>
    """)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    total = len(L) if isinstance(L, (list, dict)) else 8324
    return render_template('dashboard.html', langs=L, total=total)

# FIXED ADMIN - PRETTY TEMPLATE
@app.route('/admin')
@app.route('/admin-dashboard')
@login_required
def admin_dash():
    if current_user.role != 'admin':
        return "Access denied", 403
    users = User.query.all()
    total = len(L) if isinstance(L, (list, dict)) else 8324
    return render_template('admin.html', users=users, langs=L, total=total)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', password=generate_password_hash('admin123'), role='admin')
        db.session.add(admin_user)
        db.session.commit()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
