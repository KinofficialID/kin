import os, json, datetime
from flask import Flask, request, render_template_string, redirect, session, abort
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "kin-secret-2024")
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, "kyc"), exist_ok=True)

DATA_FILE = "posts.json"
OWNER_KEY = os.environ.get("A_PASS", "admin123")
ALLOWED_EXT = {'mp3','wav','mp4','mov','jpg','jpeg','png','gif'}

# --- Security: Block .json leak ---
@app.before_request
def block_json():
    if ".json" in request.path.lower() and "posts.json" not in request.path:
        abort(404)
    if request.path.endswith(".json") and request.path != "/posts.json":
        # Allow /posts.json via API only, block direct download sniff
        pass

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

# --- S3 Oregon West (additive) ---
def upload_to_oregon(file_obj, filename):
    try:
        if os.environ.get("AWS_ACCESS_KEY"):
            import boto3
            s3 = boto3.client('s3', region_name=os.environ.get("S3_REGION","us-west-2"),
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_KEY"))
            bucket = os.environ.get("S3_BUCKET","kin-oregon-west")
            s3.upload_fileobj(file_obj, bucket, filename)
            return f"https://{bucket}.s3.us-west-2.amazonaws.com/{filename}"
    except Exception as e:
        print("S3 fail, local fallback", e)
    file_obj.seek(0)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file_obj.save(path)
    return f"/{path}"

# --- LOGIN WITH PASSWORD - SECURE, NO BYPASS ---
USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE): 
        return {}
    try: 
        return json.load(open(USERS_FILE, encoding="utf-8"))
    except: 
        return {}

@app.route("/login", methods=["GET","POST"])
def login():
    users = load_users()
    if request.method == "POST":
        uid = request.form.get("user_id","").strip()
        pwd = request.form.get("password","").strip()
        if not uid or not pwd:
            return "Need ID and password <a href=/login>back</a>"
        # First time = register + go to KYC
        if uid not in users:
            users[uid] = {"password": pwd, "verified": False, "kyc_url": ""}
            json.dump(users, open(USERS_FILE,"w",encoding="utf-8"), indent=2)
            session["user_id"] = uid
            return redirect("/kyc")
        # Check password
        if users[uid].get("password") == pwd:
            session["user_id"] = uid
            return redirect("/")
        else:
            return "Wrong password for that ID <a href=/login>Try again</a>"
    return '''
    <h2>KIN Login - Own ID + Password</h2>
    <form method=post>
    <input name=user_id placeholder="KIN ID e.g. KIN001" required><br>
    <input name=password type=password placeholder="Your secret password" required><br>
    <button>Login / Register first time</button>
    </form>
    '''


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# --- HOME + POST ---
@app.route("/", methods=["GET","POST"])
def home():
    if "user_id" not in session:
        return redirect("/login")
    data = load_data()
    if request.method == "POST":
        text = request.form.get("text","").strip()
        t_type = request.form.get("type","word")
        tshivenda = request.form.get("tshivenda","")
        english = request.form.get("english","")
        meaning = request.form.get("meaning","")
        file_url = ""
        f = request.files.get("media")
        if f and f.filename and allowed_file(f.filename):
            fname = f"{session['user_id']}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(f.filename)}"
            file_url = upload_to_oregon(f, fname)
        if text or tshivenda or file_url:
            data.append({
                "id": len(data)+1,
                "teacher_id": session["user_id"],
                "category": t_type,
                "text": text,
                "tshivenda": tshivenda,
                "english": english,
                "meaning": meaning,
                "media": file_url,
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "views": 0
            })
            save_data(data)
        return redirect("/")
    
    posts_html = "".join([f"<div style='border:1px solid #ccc;padding:10px;margin:10px'><b>{p.get('teacher_id')} [{p.get('category')}]</b><br>{p.get('tshivenda','')}<br><i>{p.get('english','')}</i><br>{p.get('text','')}<br><small>{p.get('meaning','')}</small><br><a href='{p.get('media','')}' target=_blank>{p.get('media','')}</a><br><small>{p.get('time')}</small></div>" for p in reversed(data[-50:])])

    return render_template_string(f"""
    <h2>KIN - Your People First - Logged as {session['user_id']} | <a href=/logout>Logout</a></h2>
    <a href=/learn-earn><button>Learn & Earn R2</button></a> <a href=/kyc><button>Verify ID + Bank</button></a> <a href=/donate><button>Donate</button></a> <a href=/advertise><button>Advertise</button></a> <a href=/hq?key={OWNER_KEY}><button>HQ</button></a>
    <hr>
    <form method=post enctype=multipart/form-data>
    <select name=type><option>word</option><option>sentence</option><option>proverb</option><option>story</option><option>elder_knowledge</option><option>lesson</option><option>animation</option><option>joke</option><option>dance</option><option>live</option></select><br>
    <input name=tshivenda placeholder="Tshivenda" style="width:90%"><br>
    <input name=english placeholder="English translation" style="width:90%"><br>
    <input name=meaning placeholder="Cultural meaning" style="width:90%"><br>
    <textarea name=text placeholder="What is happening? Venda, Pedi, English..." style="width:90%"></textarea><br>
    <input type=file name=media accept="audio/*,video/*,image/*"><br>
    <button>Post to KIN</button>
    </form>
    <hr>{posts_html}
    """)

# --- NEW FEATURES (Additive files, not deleting) ---
@app.route("/learn-earn")
def learn_earn():
    if "user_id" not in session: return redirect("/login")
    return "<h2>Learn & Earn - Translate to earn R2</h2><p>Bot: Do you want to learn and earn?</p><form method=post action=/submit-translation><input name=english_phrase placeholder=English sentence><input name=tshivenda_translation placeholder=Tshivenda translation required><button>Submit - Earn R2</button></form>"

@app.route("/kyc", methods=["GET","POST"])
def kyc():
    if "user_id" not in session: return redirect("/login")
    if request.method == "POST":
        bank = request.form.get("bank_name")
        acc = request.form.get("account_no")
        pay = request.form.get("paystack_email")
        f = request.files.get("id_photo")
        url = ""
        if f and f.filename:
            fname = f"kyc_{session['user_id']}_{secure_filename(f.filename)}"
            url = upload_to_oregon(f, fname)
        d = load_data()
        d.append({"teacher_id":session["user_id"],"category":"kyc","text":f"Bank:{bank} Acc:{acc} Paystack:{pay}","media":url,"time":datetime.datetime.now().strftime("%Y-%m-%d")})
        save_data(d)
        return "ID + Bank uploaded - Awaiting HQ approval <a href=/>Back</a>"
    return '<h3>Verify ID + Bank for Payouts</h3><form method=post enctype=multipart/form-data><input name=bank_name placeholder="Bank Name"><input name=account_no placeholder="Account Number"><input name=paystack_email placeholder="Paystack Email"><input type=file name=id_photo accept="image/*" required><button>Verify</button></form>'

@app.route("/donate")
def donate():
    return '<h2>Donate to KIN</h2><p>Banks, TVs, Movie creators can fund culture.</p><a href="https://paystack.com/pay/kin-donate"><button>Donate via Paystack</button></a>'

@app.route("/advertise")
def advertise():
    return '<h2>Advertise Diverse Culture</h2><form><input placeholder="Company Name"><input placeholder="Ad Budget R"><button>Submit Ad - Await Approval</button></form>'

@app.route("/hq")
def hq():
    if request.args.get("key") != OWNER_KEY: abort(404)
    data = load_data()
    total_files = 0
    total_mb = 0
    if os.path.exists(UPLOAD_FOLDER):
        for root, dirs, files in os.walk(UPLOAD_FOLDER):
            for file in files:
                try:
                    total_mb += os.path.getsize(os.path.join(root,file))
                    total_files += 1
                except: pass
    total_mb = total_mb/1024/1024
    return render_template_string("""
    <h2>HQ - Admin Only</h2><p>Total Lessons: {{data|length}}</p><p>Total Files: {{total_files}} | MB Used: {{'%.2f' % total_mb}} MB</p>
    <p>Est Views: {{data|length * 23}} | Est Donations: R{{data|length * 5}}</p>
    <hr>{% for p in data[::-1][:30] %}<div style='border:1px solid #999;padding:5px'>{{p}}</div>{% endfor %}
    """, data=data, total_files=total_files, total_mb=total_mb)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
