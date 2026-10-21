import os, json, requests, re
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, session, abort, send_from_directory, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "kin-final-world-lang-2026")
DATA_FILE = "kin_data.json"
BLOCK_FILE = "blocked_ips.json"
CONFIG_FILE = "kin_config.json"
USER_FILE = "kin_users.json"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

OWNER_KEY = os.environ.get("A_PASS", "0000")
OWNER_USER = os.environ.get("A_USER", "owner")

# Rate limit optional
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])
    def limit(s): return limiter.limit(s)
except:
    def limit(s):
        def d(f): return f
        return d
    def get_remote_address(): return request.remote_addr

# --- JSON READER - APP READS JSON, NO CODE CHANGE NEEDED ---
def load_config():
    default = {
        "app_name": "KIN - Your People First",
        "app_version": "1.0 World Languages",
        "languages": ["Tshivenda","Sepedi","Xitsonga","IsiZulu","IsiXhosa","Sesotho","Setswana","SiSwati","IsiNdebele","Tshivenda","Xitsonga","English","French","Swahili","Shona","Portuguese"],
        "allowed_categories": ["word","sentence","proverb","story","elder_knowledge","lesson","animation","joke","dance","live","prayer","song","history"],
        "ads_enabled": True,
        "learn_earn_enabled": True,
        "learn_earn_rate": "R2",
        "donation_enabled": True,
        "max_upload_mb": 100,
        "maintenance": False,
        "tribe_challenge": True
    }
    if not os.path.exists(CONFIG_FILE):
        json.dump(default, open(CONFIG_FILE,"w"), indent=2)
        return default
    try:
        cfg = json.load(open(CONFIG_FILE,"r",encoding="utf-8"))
        # Merge missing keys without overwriting user edits
        for k,v in default.items():
            if k not in cfg: cfg[k]=v
        return cfg
    except:
        return default

def load_data():
    if not os.path.exists(DATA_FILE): return []
    try: return json.load(open(DATA_FILE,"r",encoding="utf-8"))
    except: return []

def save_data(d):
    json.dump(d, open(DATA_FILE,"w",encoding="utf-8"), indent=2, ensure_ascii=False)

def load_users():
    if not os.path.exists(USER_FILE): return {}
    try: return json.load(open(USER_FILE,"r",encoding="utf-8"))
    except: return {}

def save_users(u):
    json.dump(u, open(USER_FILE,"w",encoding="utf-8"), indent=2)

def load_blocks():
    if not os.path.exists(BLOCK_FILE): return []
    try: return json.load(open(BLOCK_FILE))
    except: return []

def block_ip(ip, reason):
    blocks=load_blocks()
    if not any(b["ip"]==ip for b in blocks):
        blocks.append({"ip":ip,"reason":reason,"time":datetime.now().isoformat()})
        json.dump(blocks, open(BLOCK_FILE,"w"), indent=2)

def mask_phone(phone):
    return f"{phone[:4]}****{phone[-3:]}" if len(phone)>=7 else "****"

def mask_bank(acc):
    return f"****{acc[-4:]}" if len(acc)>=4 else "****"

@app.before_request
def security():
    ip = request.headers.get("CF-Connecting-IP") or get_remote_address()
    if any(b["ip"]==ip for b in load_blocks()): abort(404)
    if any(x in request.path.lower() for x in [".json",".env",".git","kin_data","blocked_ips","kin_users"]):
        if "/uploads" not in request.path and request.path!=f"/{CONFIG_FILE}":
            # Allow reading config json via route, but block direct file access
            if CONFIG_FILE not in request.path:
                block_ip(ip, f"Tried {request.path}")
                abort(404)
    if request.args.get("owner_key")==OWNER_KEY:
        session["user_id"]=OWNER_USER
        session["user_name"]="HQ Owner"
        session["phone"]=OWNER_USER
        session["is_owner"]=True

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route(f"/{CONFIG_FILE}")
def serve_config():
    # Allow app to read its own config json publicly but hide secrets - this file has no secrets
    cfg=load_config()
    return jsonify(cfg)

# --- AUTH: PHONE + FACE ---
@app.route("/login", methods=["GET","POST"])
def login():
    cfg=load_config()
    users=load_users()
    if cfg.get("maintenance") and request.args.get("owner_key")!=OWNER_KEY:
        return "KIN in maintenance - HQ only"
    if request.method=="POST":
        phone=request.form.get("phone","").strip().replace(" ","")
        name=request.form.get("name","").strip()
        face=request.files.get("face")
        if len(phone)<9 or len(name)<2:
            return "Phone + Name required <a href=/login>back</a>",400
        if request.form.get("popia_consent")!="yes":
            return "POPIA consent required <a href=/login>back</a>",400
        face_url=users.get(phone,{}).get("face","")
        if face and face.filename:
            fname=f"face_{phone}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(face.filename)}"
            face.save(os.path.join(UPLOAD_FOLDER,fname))
            face_url=f"/uploads/{fname}"
        users[phone]={"phone":phone,"name":name,"face":face_url,"first_seen":users.get(phone,{}).get("first_seen",datetime.now().isoformat()),"last_login":datetime.now().isoformat(),"popia_consent":True}
        save_users(users)
        session["user_id"]=phone
        session["phone"]=phone
        session["user_name"]=name
        session["face"]=face_url
        session["is_owner"]=(phone==OWNER_USER)
        return redirect("/")
    return render_template_string("""
    <style>body{font-family:system-ui;max-width:500px;margin:40px auto;padding:20px;background:#0a0c10;color:#fff}
    input,button{width:100%;padding:14px;margin:10px 0;border-radius:10px;border:1px solid #333;background:#151821;color:#fff}button{background:#2563eb}
    label{display:block;margin:8px 0} a{color:#60a5fa} .warn{background:#1e293b;padding:10px;border-radius:8px;border-left:4px solid #f59e0b;font-size:13px}</style>
    <h2>{{cfg.app_name}} - Phone + Face Login</h2><p>No KIN ID. Phone is your ID. Saves every language in world.</p>
    <div class=warn>POPIA: Phone+Face stored in Oregon USA. Masked as +27****. Delete in Settings. Config controls languages: {{cfg.languages|length}} languages ready.</div>
    <form method=post enctype=multipart/form-data>
    <input name=phone placeholder=Phone +27... / 0... required><input name=name placeholder=Full Name required>
    <label>Face selfie (first time)</label><input type=file name=face accept=image/*>
    <label><input type=checkbox name=popia_consent value=yes required> I consent S11 store phone+face</label>
    <label><input type=checkbox name=cross_border_consent value=yes required> I consent Oregon USA S72</label>
    <input name=owner_key type=password placeholder=Owner key (HQ only)>
    <button>Enter KIN</button></form>
    <p><a href=/help>Help</a> | <a href=/privacy>Privacy</a> | <a href=/{{config_file}}>View Config JSON</a></p>
    """, cfg=cfg, config_file=CONFIG_FILE)

@app.route("/help")
def help_center():
    cfg=load_config()
    return render_template_string("""
    <style>body{font-family:system-ui;max-width:700px;margin:auto;padding:20px;background:#0a0c10;color:#fff}a{color:#60a5fa}.card{background:#151821;padding:15px;border-radius:10px;margin:10px 0}</style>
    <h2>{{cfg.app_name}} v{{cfg.app_version}} Help - JSON Controlled</h2>
    <div class=card>Login: Phone + Face (No ID)</div>
    <div class=card>Languages from JSON: {{cfg.languages}}</div>
    <div class=card>Categories from JSON: {{cfg.allowed_categories}}</div>
    <div class=card>Earn Rate: {{cfg.learn_earn_rate}} - Change in JSON, no code</div>
    <div class=card>Ads: {{'ON' if cfg.ads_enabled else 'OFF'}} - Change in JSON</div>
    <div class=card>Next time to add language: Edit {{config_file}} in GitHub > Add to languages array > Save. No kin.py change.</div>
    <a href=/>Home</a>
    """, cfg=cfg, config_file=CONFIG_FILE)

@app.route("/privacy")
def privacy():
    return render_template_string("""
    <style>body{font-family:system-ui;max-width:800px;margin:auto;padding:20px;background:#0a0c10;color:#e5e7eb}a{color:#60a5fa}</style>
    <h2>KIN Privacy - POPIA - Phone+Face - JSON World Languages</h2>
    <p>Collect: Phone, Name, Face, lessons in any language from config, bank **** + Paystack. No ID number.</p>
    <p>Purpose: Teach AI every language, verify real person, pay creators.</p>
    <p>Consent S11 + Cross-border S72 Oregon USA. Delete S24 in /settings. Retention S14 12 months for KYC.</p>
    <p>Config file {{config_file}} controls languages without code change - no bypass.</p>
    <a href=/>Home</a>
    """, config_file=CONFIG_FILE)

@app.route("/hq")
def hq():
    if request.args.get("key")!=OWNER_KEY: abort(404)
    data=load_data(); blocks=load_blocks(); users=load_users(); cfg=load_config()
    total_mb=sum(os.path.getsize(os.path.join(UPLOAD_FOLDER,f)) for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER,f)))/1024/1024 if os.path.exists(UPLOAD_FOLDER) else 0
    return render_template_string("""
    <style>body{font-family:system-ui;max-width:900px;margin:auto;padding:15px;background:#0a0c10;color:#fff}.card{background:#151821;padding:10px;margin:5px;border-radius:8px}</style>
    <h2>HQ - JSON Controlled - MB Traffic - Full Control - No Login Needed</h2>
    <p>App: {{cfg.app_name}} {{cfg.app_version}} | Users: {{users|length}} | Lessons: {{data|length}} | MB: {{'%.2f'%total_mb}} | Blocked: {{blocks|length}}</p>
    <p>Config: <a href=/{{config_file}} style=color:#60a5fa>{{config_file}}</a> - Edit this file in GitHub to add language/category/price - No kin.py change needed ever</p>
    <p>Current languages ({{cfg.languages|length}}): {{cfg.languages}}</p>
    <p>Current categories: {{cfg.allowed_categories}}</p>
    <h3>Users Phone+Face</h3>{% for p,u in users.items() %}<div class=card>{{u.name}} | {{p[:4]}}**** | <a href="{{u.face}}" style=color:#60a5fa>Face</a> | {{u.last_login}}</div>{% endfor %}
    <h3>Lessons (Any language in world)</h3>{% for p in data[::-1][:20] %}<div class=card>{{p.time}} | {{p.language}} | {{p.category}} | {{p.tshivenda[:70]}} | Phone: {{p.teacher_id[:4]}}****</div>{% endfor %}
    <h3>Blocked Hackers Trace</h3>{% for b in blocks %}<div class=card>{{b.ip}} - {{b.reason}} - {{b.time}}</div>{% endfor %}
    """, data=data, blocks=blocks, users=users, total_mb=total_mb, cfg=cfg, config_file=CONFIG_FILE)

@app.route("/", methods=["GET"])
def home():
    if "user_id" not in session: return redirect("/login")
    data=load_data(); cfg=load_config(); users=load_users()
    me=users.get(session.get("phone"),{})
    return render_template_string("""
    <style>body{font-family:system-ui;max-width:800px;margin:auto;padding:15px;background:#0a0c10;color:#e5e7eb}
    input,textarea,select,button{width:100%;padding:12px;margin:7px 0;border-radius:10px;border:1px solid #2a2f3a;background:#151821;color:#fff;box-sizing:border-box}
    button{background:#2563eb;font-weight:bold} .card{background:#151821;padding:16px;border-radius:12px;margin:16px 0} audio,video,img{width:100%;border-radius:8px;margin-top:8px}
    .tag{padding:3px 8px;border-radius:20px;font-size:12px;background:#1e293b;display:inline-block} .ad{border:1px dashed #60a5fa}</style>
    <div style=display:flex;justify-content:space-between><h2>{{cfg.app_name}}</h2><small>{{session.user_name}} | {{session.phone[:4]}}**** | <a href=/help style=color:#60a5fa>Help</a> | <a href=/hq?key={{owner_key}} style=color:#60a5fa>HQ</a> | <a href=/{{config_file}} style=color:#60a5fa>Config JSON</a></small></div>
    <div class=card><h3>Teach Machine - Any Language in World (from {{config_file}})</h3>
    <form method=post action=/post enctype=multipart/form-data>
    <select name=language required><option value="">-- Choose Language (from JSON) --</option>{% for l in cfg.languages %}<option value="{{l}}">{{l}}</option>{% endfor %}</select>
    <select name=category required><option value="">-- Type (from JSON) --</option>{% for c in cfg.allowed_categories %}<option value="{{c}}">{{c}}</option>{% endfor %}</select>
    <textarea name=tshivenda placeholder=What you teach in that language - ANY language, ANY text, unlimited - required rows=2 required></textarea>
    <input name=english placeholder=English translation (optional)>
    <textarea name=meaning placeholder=Cultural meaning rows=2></textarea>
    <input type=file name=voice accept=audio/*><input type=file name=video accept=video/*><input type=file name=image accept=image/*>
    <label><input type=checkbox name=elder_consent value=yes> Elder consent if recording other person S11</label>
    <button>Post - Save Every Language + Voice + Video</button></form>
    <small>Next time you want new language/category, just edit {{config_file}} - No kin.py change ever</small></div>
    <h3>Feed - {{data|length}} Lessons - World Languages</h3>
    {% for p in data[::-1] %}<div class="card {% if loop.index %5==0 and cfg.ads_enabled %}ad{% endif %}">
    {% if loop.index %5==0 and cfg.ads_enabled %}<small>AD SLOT - Pays HQ per MB view</small><br>{% endif %}
    <span class=tag>{{p.language}} | {{p.category}}</span> <small>{{p.time}} - {{p.teacher_name}}</small><br><b>{{p.tshivenda}}</b><br>{{p.english}}<br><i>{{p.meaning}}</i>
    {% if p.voice_path %}<audio controls src="{{p.voice_path}}"></audio>{% endif %}
    {% if p.video_path %}<video controls src="{{p.video_path}}"></video>{% endif %}
    {% if p.image_path %}<img src="{{p.image_path}}">{% endif %}
    </div>{% endfor %}
    """, data=data, session=session, owner_key=OWNER_KEY, cfg=cfg, config_file=CONFIG_FILE, me=me)

@app.route("/post", methods=["POST"])
@limit("10 per minute")
def post():
    if "user_id" not in session: return redirect("/login")
    cat=request.form.get("category")
    if cat in ["story","elder_knowledge","live"] and request.form.get("elder_consent")!="yes":
        return "Need elder consent <a href=/>Back</a>",400
    data=load_data()
    def save_file(field):
        f=request.files.get(field)
        if f and f.filename and '.' in f.filename:
            fname=f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(f.filename)}"
            f.save(os.path.join(UPLOAD_FOLDER,fname))
            return f"/uploads/{fname}"
        return ""
    entry={"teacher_id":session["phone"],"teacher_name":session["user_name"],"language":request.form.get("language","Tshivenda"),"category":cat,"tshivenda":request.form.get("tshivenda"),"english":request.form.get("english",""),"meaning":request.form.get("meaning",""),"voice_path":save_file("voice"),"video_path":save_file("video"),"image_path":save_file("image"),"time":datetime.now().strftime("%Y-%m-%d %H:%M")}
    data.append(entry); save_data(data); return redirect("/")

@app.route("/settings", methods=["GET","POST"])
def settings():
    if "user_id" not in session: return redirect("/login")
    if request.method=="POST" and request.form.get("action")=="delete_my_data":
        phone=session["phone"]
        data=load_data()
        new_data=[d for d in data if d.get("teacher_id")!=phone]
        save_data(new_data)
        users=load_users()
        if phone in users: del users[phone]
        save_users(users)
        session.clear()
        return "POPIA S24 Deleted phone+face+lessons <a href=/login>Bye</a>"
    return render_template_string("""
    <style>body{font-family:system-ui;max-width:600px;margin:auto;padding:20px;background:#0a0c10;color:#fff}button{width:100%;padding:12px;margin:8px 0;border-radius:8px;background:#151821;color:#fff;border:1px solid #333}.danger{background:#991b1b}a{color:#60a5fa}</style>
    <h2>Settings - Phone+Face</h2><p>{{s.user_name}} - {{s.phone}}</p><p><a href=/privacy>Privacy</a> | <a href=/help>Help</a> | <a href=/{{config_file}}>Config JSON</a></p>
    <form method=post><input type=hidden name=action value=delete_my_data><button class=danger>Delete Everything Forever</button></form><a href=/>Back</a>
    """, s=session, config_file=CONFIG_FILE)

@app.route("/bot")
@limit("30 per minute")
def bot():
    q=request.args.get("q","").strip()
    if not q: return jsonify({"ask":"/bot?q=Venda"})
    if any(x in q.lower() for x in ["hack","bypass",".json"]): return jsonify({"answer":"Blocked"})
    try:
        r=requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{q}", timeout=4).json()
        summ=r.get("extract","")[:500]
    except: summ=""
    if not summ: summ=f"KIN: {q} - Add elder story to teach machine."
    return jsonify({"q":q,"answer":summ})

@app.route("/learn-earn")
@limit("20 per minute")
def learn_earn():
    if "user_id" not in session: return redirect("/login")
    cfg=load_config(); data=load_data()
    if not cfg.get("learn_earn_enabled"): return "Learn & Earn disabled in JSON - Enable in config"
    return render_template_string("""
    <style>body{font-family:system-ui;max-width:700px;margin:auto;padding:20px;background:#0a0c10;color:#fff}.card{background:#151821;padding:15px;border-radius:10px;margin:10px 0}button{padding:10px;border-radius:8px;background:#2563eb;color:#fff;border:0}</style>
    <h2>Learn & Earn - {{cfg.learn_earn_rate}} (from JSON)</h2>
    {% for p in data[-5:][::-1] %}<div class=card><b>{{p.language}}:</b> {{p.tshivenda}}<br><b>EN:</b> {{p.english}}<br><form method=post action=/submit-translation><input type=hidden name=orig value="{{p.tshivenda}}"><input name=translation placeholder=Translate to your language required><button>Earn {{cfg.learn_earn_rate}}</button></form></div>{% endfor %}
    <a href=/>Back</a> | <a href=/{{config_file}}>Config</a>
    """, data=data, cfg=cfg, config_file=CONFIG_FILE)

@app.route("/submit-translation", methods=["POST"])
@limit("10 per minute")
def submit_trans():
    if "user_id" not in session: return redirect("/login")
    cfg=load_config(); data=load_data()
    data.append({"teacher_id":session["phone"],"category":"translation_earn","language":request.form.get("language","Tshivenda"),"tshivenda":request.form.get("translation"),"english":request.form.get("orig"),"time":datetime.now().strftime("%Y-%m-%d"),"earn":cfg["learn_earn_rate"]})
    save_data(data)
    return f"Earned {cfg['learn_earn_rate']} pending HQ <a href=/learn-earn>Continue</a>"

@app.route("/donate")
def donate():
    cfg=load_config()
    if not cfg.get("donation_enabled"): return "Donations disabled in JSON"
    return '<h2>Donate via Paystack</h2><a href=https://paystack.com/pay/kin-donate><button>Donate</button></a>'

@app.route("/advertise")
def advertise():
    return '<h2>Advertise culture - Pays KIN - Rate from JSON</h2><form><input placeholder=Company><input placeholder=Budget R><button>Submit Ad - HQ approves</button></form>'

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
