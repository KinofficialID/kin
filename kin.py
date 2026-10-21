import os, json, requests
from datetime import datetime
from flask import Flask, request, render_template_string, redirect, session, abort, send_from_directory, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "kin-final-world-lang-2026")
DATA_FILE = "kin_data.json"
BLOCK_FILE = "blocked_ips.json"
CONFIG_FILE = "kin_config.json"
USER_FILE = "kin_users.json"
CHAT_FILE = "kin_chats.json"
FRIEND_FILE = "kin_friends.json"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

OWNER_KEY = os.environ.get("A_PASS", "0000")
OWNER_USER = os.environ.get("A_USER", "owner")

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

def load_config():
    default = {
        "app_name": "KIN - Your People First",
        "app_version": "2.0 Chat + World",
        "languages": ["Tshivenda","Sepedi","Xitsonga","IsiZulu","IsiXhosa","Sesotho","Setswana","SiSwati","IsiNdebele","English","French","Swahili","Shona","Portuguese"],
        "allowed_categories": ["word","sentence","proverb","story","elder_knowledge","lesson","animation","joke","dance","live","prayer","song","history"],
        "ads_enabled": True,
        "learn_earn_enabled": True,
        "learn_earn_rate": "R2",
        "donation_enabled": True,
        "chat_enabled": True,
        "chat_needs_request": True,
        "max_upload_mb": 100,
        "maintenance": False
    }
    if not os.path.exists(CONFIG_FILE):
        json.dump(default, open(CONFIG_FILE,"w"), indent=2)
        return default
    try:
        cfg = json.load(open(CONFIG_FILE,"r",encoding="utf-8"))
        for k,v in default.items():
            if k not in cfg: cfg[k]=v
        return cfg
    except:
        return default

def load_data():
    if not os.path.exists(DATA_FILE): return []
    try: return json.load(open(DATA_FILE,"r",encoding="utf-8"))
    except: return []
def save_data(d): json.dump(d, open(DATA_FILE,"w",encoding="utf-8"), indent=2, ensure_ascii=False)
def load_users():
    if not os.path.exists(USER_FILE): return {}
    try: return json.load(open(USER_FILE,"r",encoding="utf-8"))
    except: return {}
def save_users(u): json.dump(u, open(USER_FILE,"w",encoding="utf-8"), indent=2)
def load_blocks():
    if not os.path.exists(BLOCK_FILE): return []
    try: return json.load(open(BLOCK_FILE))
    except: return []
def block_ip(ip, reason):
    blocks=load_blocks()
    if not any(b["ip"]==ip for b in blocks):
        blocks.append({"ip":ip,"reason":reason,"time":datetime.now().isoformat()})
        json.dump(blocks, open(BLOCK_FILE,"w"), indent=2)
def load_chats():
    if not os.path.exists(CHAT_FILE): return []
    try: return json.load(open(CHAT_FILE,"r",encoding="utf-8"))
    except: return []
def save_chats(c): json.dump(c, open(CHAT_FILE,"w",encoding="utf-8"), indent=2)
def load_friends():
    if not os.path.exists(FRIEND_FILE): return {}
    try: return json.load(open(FRIEND_FILE,"r",encoding="utf-8"))
    except: return {}
def save_friends(f): json.dump(f, open(FRIEND_FILE,"w"), indent=2)
def mask_phone(phone): return f"{phone[:4]}****{phone[-3:]}" if len(phone)>=7 else "****"

@app.before_request
def security():
    ip = request.headers.get("CF-Connecting-IP") or get_remote_address()
    if any(b["ip"]==ip for b in load_blocks()): abort(404)
    if any(x in request.path.lower() for x in [".json",".env",".git","kin_data","blocked_ips","kin_users"]):
        if "/uploads" not in request.path and CONFIG_FILE not in request.path:
            block_ip(ip, f"Tried {request.path}")
            abort(404)
    if request.args.get("owner_key")==OWNER_KEY:
        session["user_id"]=OWNER_USER; session["user_name"]="HQ Owner"; session["phone"]=OWNER_USER; session["is_owner"]=True

@app.route("/uploads/<path:filename>")
def serve_upload(filename): return send_from_directory(UPLOAD_FOLDER, filename)
@app.route(f"/{CONFIG_FILE}")
def serve_config(): return jsonify(load_config())

@app.route("/login", methods=["GET","POST"])
def login():
    cfg=load_config(); users=load_users()
    if cfg.get("maintenance") and request.args.get("owner_key")!=OWNER_KEY: return "Maintenance HQ only"
    if request.method=="POST":
        phone=request.form.get("phone","").strip().replace(" ",""); name=request.form.get("name","").strip(); face=request.files.get("face")
        if len(phone)<9 or len(name)<2: return "Phone + Name required <a href=/login>back</a>",400
        if request.form.get("popia_consent")!="yes": return "POPIA required <a href=/login>back</a>",400
        face_url=users.get(phone,{}).get("face","")
        if face and face.filename:
            fname=f"face_{phone}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(face.filename)}"
            face.save(os.path.join(UPLOAD_FOLDER,fname)); face_url=f"/uploads/{fname}"
        users[phone]={"phone":phone,"name":name,"face":face_url,"first_seen":users.get(phone,{}).get("first_seen",datetime.now().isoformat()),"last_login":datetime.now().isoformat(),"popia_consent":True}
        save_users(users)
        session["user_id"]=phone; session["phone"]=phone; session["user_name"]=name; session["face"]=face_url
        return redirect("/")
    return render_template_string("""
    <style>body{font-family:system-ui;max-width:500px;margin:40px auto;padding:20px;background:#0a0c10;color:#fff}
    input,button{width:100%;padding:14px;margin:10px 0;border-radius:10px;border:1px solid #333;background:#151821;color:#fff}button{background:#2563eb}label{display:block;margin:8px 0}a{color:#60a5fa}</style>
    <h2>{{cfg.app_name}} - Phone+Face - Chat Ready</h2><p>No KIN ID. Phone is ID. Saves every language + chat if accepted.</p>
    <form method=post enctype=multipart/form-data>
    <input name=phone placeholder=Phone +27... / 0... required><input name=name placeholder=Full Name required>
    <label>Face selfie (first time)</label><input type=file name=face accept=image/*>
    <label><input type=checkbox name=popia_consent value=yes required> Consent store phone+face S11</label>
    <label><input type=checkbox name=cross_border_consent value=yes required> Consent Oregon USA S72</label>
    <input name=owner_key type=password placeholder=Owner key HQ only><button>Enter KIN</button></form>
    <p><a href=/help>Help</a> | <a href=/privacy>Privacy</a></p>
    """, cfg=cfg)

@app.route("/friends", methods=["GET","POST"])
def friends():
    if "phone" not in session: return redirect("/login")
    cfg=load_config()
    if not cfg.get("chat_enabled"): return "Chat disabled in JSON"
    me=session["phone"]; fr=load_friends(); users=load_users()
    if request.method=="POST":
        target=request.form.get("target_phone","").strip().replace(" ",""); action=request.form.get("action")
        if not target or target==me: return "Invalid <a href=/friends>back</a>"
        my=fr.get(me, {"requests_sent":[],"requests_received":[],"friends":[]})
        their=fr.get(target, {"requests_sent":[],"requests_received":[],"friends":[]})
        if action=="send":
            if target not in my["friends"] and target not in my["requests_sent"] and target in users:
                my["requests_sent"].append(target); their["requests_received"].append(me)
        elif action=="accept":
            if target in my["requests_received"]:
                my["friends"].append(target); their["friends"].append(me)
                my["requests_received"]=[x for x in my["requests_received"] if x!=target]
                their["requests_sent"]=[x for x in their["requests_sent"] if x!=me]
        elif action=="reject":
            my["requests_received"]=[x for x in my["requests_received"] if x!=target]
            their["requests_sent"]=[x for x in their["requests_sent"] if x!=me]
        fr[me]=my; fr[target]=their; save_friends(fr)
        return redirect("/friends")
    my=fr.get(me, {"requests_sent":[],"requests_received":[],"friends":[]})
    return render_template_string("""
    <style>body{font-family:system-ui;max-width:700px;margin:auto;padding:20px;background:#0a0c10;color:#fff}
    .card{background:#151821;padding:12px;border-radius:10px;margin:8px 0}input,button{padding:10px;border-radius:8px;background:#151821;color:#fff;border:1px solid #333}button{background:#2563eb}a{color:#60a5fa}</style>
    <h2>Friends - Request → Accept → Chat ✅</h2><p>Me: {{me}}</p>
    <div class=card><form method=post><input name=target_phone placeholder=Friend Phone +27... required><input type=hidden name=action value=send><button>Send Request</button></form></div>
    <h3>Requests Received</h3>{% for p in my.requests_received %}<div class=card>{{p}} {{users.get(p,{}).get('name','')}}
    <form method=post style=display:inline><input type=hidden name=target_phone value="{{p}}"><input type=hidden name=action value=accept><button>Accept Chat</button></form>
    <form method=post style=display:inline><input type=hidden name=target_phone value="{{p}}"><input type=hidden name=action value=reject><button style=background:#991b1b>Reject</button></form></div>{% endfor %}
    <h3>My Friends - Chat Now</h3>{% for p in my.friends %}<div class=card>{{p}} {{users.get(p,{}).get('name','')}} <a href=/chat?with={{p}}><button>Open Chat</button></a></div>{% endfor %}
    <a href=/>Home</a> | <a href=/chat-list>All Chats</a>
    """, me=me, my=my, users=users)

@app.route("/chat")
def chat():
    if "phone" not in session: return redirect("/login")
    cfg=load_config(); me=session["phone"]; with_phone=request.args.get("with")
    if not with_phone: return redirect("/friends")
    fr=load_friends(); my=fr.get(me, {"friends":[]})
    if cfg.get("chat_needs_request") and with_phone not in my["friends"]: return "Must accept first <a href=/friends>Friends</a>",403
    chats=load_chats(); room=[c for c in chats if (c["from"]==me and c["to"]==with_phone) or (c["from"]==with_phone and c["to"]==me)]
    users=load_users()
    return render_template_string("""
    <style>body{font-family:system-ui;max-width:700px;margin:auto;padding:15px;background:#0a0c10;color:#fff}
    .card{background:#151821;padding:10px;border-radius:10px;margin:6px 0} .me{background:#1e3a8a;margin-left:20px} input,button{padding:12px;border-radius:8px;border:1px solid #333;background:#151821;color:#fff;width:100%;box-sizing:border-box}button{background:#2563eb;margin-top:8px}a{color:#60a5fa}</style>
    <h2>Chat {{users.get(me,{}).get('name','')}} ↔ {{users.get(with_phone,{}).get('name',with_phone)}} ✅</h2>
    {% for c in room %}<div class="card {% if c.from==me %}me{% endif %}"><small>{{c.time}} {{c.from[:4]}}****</small><br>{{c.msg}}</div>{% endfor %}
    <form method=post action=/chat-send><input type=hidden name=to value="{{with_phone}}"><input name=msg placeholder=Message any language required required><button>Send</button></form>
    <a href=/friends>Friends</a> | <a href=/>Home</a>
    """, me=me, with_phone=with_phone, room=room, users=users)

@app.route("/chat-send", methods=["POST"])
@limit("30 per minute")
def chat_send():
    if "phone" not in session: return redirect("/login")
    me=session["phone"]; to=request.form.get("to","").strip(); msg=request.form.get("msg","").strip()
    if not msg or not to: return redirect(f"/chat?with={to}")
    chats=load_chats(); chats.append({"from":me,"to":to,"msg":msg[:2000],"time":datetime.now().strftime("%Y-%m-%d %H:%M")})
    save_chats(chats); return redirect(f"/chat?with={to}")

@app.route("/chat-list")
def chat_list():
    if "phone" not in session: return redirect("/login")
    me=session["phone"]; chats=load_chats(); users=load_users()
    partners=set([c["to"] for c in chats if c["from"]==me] + [c["from"] for c in chats if c["to"]==me])
    return render_template_string("""
    <style>body{font-family:system-ui;max-width:700px;margin:auto;padding:20px;background:#0a0c10;color:#fff}.card{background:#151821;padding:12px;border-radius:10px;margin:8px 0}a{color:#60a5fa}button{padding:8px;border-radius:8px;background:#2563eb;color:#fff;border:0}</style>
    <h2>All Chats</h2>{% for p in partners %}<div class=card>{{p}} {{users.get(p,{}).get('name','')}} <a href=/chat?with={{p}}><button>Open</button></a></div>{% else %}<p>No chats</p>{% endfor %}
    <a href=/friends>Friends</a> | <a href=/>Home</a>
    """, me=me, partners=partners, users=users)

@app.route("/help")
def help_center():
    cfg=load_config()
    return render_template_string("""
    <style>body{font-family:system-ui;max-width:700px;margin:auto;padding:20px;background:#0a0c10;color:#fff}a{color:#60a5fa}.card{background:#151821;padding:15px;border-radius:10px;margin:10px 0}</style>
    <h2>{{cfg.app_name}} {{cfg.app_version}} Help</h2>
    <div class=card>Chat: /friends → Send Request by Phone → Accept → Chat opens. Any language.</div>
    <div class=card>Languages from JSON: {{cfg.languages}}</div>
    <div class=card>To add language: Edit kin_config.json → Save. No code.</div>
    <a href=/>Home</a>
    """, cfg=cfg)

@app.route("/privacy")
def privacy():
    return render_template_string("""<style>body{font-family:system-ui;max-width:800px;margin:auto;padding:20px;background:#0a0c10;color:#e5e7eb}a{color:#60a5fa}</style>
    <h2>Privacy POPIA Phone+Face+Chat</h2><p>Phone masked, face stored Oregon, chats stored Oregon, delete in /settings S24.</p><a href=/>Home</a>""")

@app.route("/hq")
def hq():
    if request.args.get("key")!=OWNER_KEY: abort(404)
    data=load_data(); blocks=load_blocks(); users=load_users(); cfg=load_config(); chats=load_chats()
    total_mb=sum(os.path.getsize(os.path.join(UPLOAD_FOLDER,f)) for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER,f)))/1024/1024 if os.path.exists(UPLOAD_FOLDER) else 0
    return render_template_string("""
    <style>body{font-family:system-ui;max-width:900px;margin:auto;padding:15px;background:#0a0c10;color:#fff}.card{background:#151821;padding:10px;margin:5px;border-radius:8px}</style>
    <h2>HQ - Chat + World - {{cfg.app_version}}</h2>
    <p>Users {{users|length}} | Lessons {{data|length}} | Chats {{chats|length}} | MB {{'%.2f'%total_mb}}</p>
    <p>Chat ON: {{cfg.chat_enabled}} Need Request: {{cfg.chat_needs_request}} - Edit JSON to change</p>
    {% for c in chats[::-1][:20] %}<div class=card>{{c.time}} {{c.from[:4]}}**** → {{c.to[:4]}}**** : {{c.msg[:80]}}</div>{% endfor %}
    """, data=data, blocks=blocks, users=users, total_mb=total_mb, cfg=cfg, chats=chats)

@app.route("/", methods=["GET"])
def home():
    if "user_id" not in session: return redirect("/login")
    data=load_data(); cfg=load_config()
    return render_template_string("""
    <style>body{font-family:system-ui;max-width:800px;margin:auto;padding:15px;background:#0a0c10;color:#e5e7eb}
    input,textarea,select,button{width:100%;padding:12px;margin:7px 0;border-radius:10px;border:1px solid #2a2f3a;background:#151821;color:#fff;box-sizing:border-box}
    button{background:#2563eb;font-weight:bold} .card{background:#151821;padding:16px;border-radius:12px;margin:16px 0}
    .tag{padding:3px 8px;border-radius:20px;font-size:12px;background:#1e293b;display:inline-block}</style>
    <div style=display:flex;justify-content:space-between><h2>{{cfg.app_name}} {% if cfg.chat_enabled %}💬{% endif %}</h2><small>{{session.user_name}} | <a href=/friends style=color:#60a5fa>Friends/Chat</a> | <a href=/hq?key={{owner_key}} style=color:#60a5fa>HQ</a></small></div>
    <div class=card><h3>Teach Machine - Any Language from JSON</h3>
    <form method=post action=/post enctype=multipart/form-data>
    <select name=language required><option value="">Language (JSON)</option>{% for l in cfg.languages %}<option value="{{l}}">{{l}}</option>{% endfor %}</select>
    <select name=category required><option value="">Type (JSON)</option>{% for c in cfg.allowed_categories %}<option value="{{c}}">{{c}}</option>{% endfor %}</select>
    <textarea name=tshivenda placeholder=Any language any text required rows=2 required></textarea>
    <input name=english placeholder=English><textarea name=meaning placeholder=Meaning rows=2></textarea>
    <input type=file name=voice accept=audio/*><input type=file name=video accept=video/*><input type=file name=image accept=image/*>
    <label><input type=checkbox name=elder_consent value=yes> Elder consent</label><button>Post</button></form></div>
    <h3>Feed {{data|length}}</h3>{% for p in data[::-1] %}<div class=card><span class=tag>{{p.language}} | {{p.category}}</span> {{p.time}} {{p.teacher_name}}<br><b>{{p.tshivenda}}</b><br>{{p.english}}</div>{% endfor %}
    """, data=data, session=session, owner_key=OWNER_KEY, cfg=cfg)

@app.route("/post", methods=["POST"])
@limit("10 per minute")
def post():
    if "user_id" not in session: return redirect("/login")
    if request.form.get("category") in ["story","elder_knowledge","live"] and request.form.get("elder_consent")!="yes": return "Need elder consent",400
    data=load_data()
    def save_file(field):
        f=request.files.get(field)
        if f and f.filename and '.' in f.filename:
            fname=f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(f.filename)}"
            f.save(os.path.join(UPLOAD_FOLDER,fname)); return f"/uploads/{fname}"
        return ""
    entry={"teacher_id":session["phone"],"teacher_name":session["user_name"],"language":request.form.get("language","Tshivenda"),"category":request.form.get("category"),"tshivenda":request.form.get("tshivenda"),"english":request.form.get("english",""),"meaning":request.form.get("meaning",""),"voice_path":save_file("voice"),"video_path":save_file("video"),"image_path":save_file("image"),"time":datetime.now().strftime("%Y-%m-%d %H:%M")}
    data.append(entry); save_data(data); return redirect("/")

@app.route("/settings", methods=["GET","POST"])
def settings():
    if "user_id" not in session: return redirect("/login")
    if request.method=="POST" and request.form.get("action")=="delete_my_data":
        phone=session["phone"]; save_data([d for d in load_data() if d.get("teacher_id")!=phone])
        save_chats([c for c in load_chats() if c["from"]!=phone and c["to"]!=phone])
        fr=load_friends()
        if phone in fr: del fr[phone]
        for k in list(fr.keys()):
            fr[k]["friends"]=[x for x in fr[k].get("friends",[]) if x!=phone]
            fr[k]["requests_sent"]=[x for x in fr[k].get("requests_sent",[]) if x!=phone]
            fr[k]["requests_received"]=[x for x in fr[k].get("requests_received",[]) if x!=phone]
        save_friends(fr)
        users=load_users()
        if phone in users: del users[phone]; save_users(users)
        session.clear(); return "Deleted all including chats S24 <a href=/login>Bye</a>"
    return render_template_string("""
    <style>body{font-family:system-ui;max-width:600px;margin:auto;padding:20px;background:#0a0c10;color:#fff}button{width:100%;padding:12px;margin:8px 0;border-radius:8px;background:#151821;color:#fff;border:1px solid #333}.danger{background:#991b1b}a{color:#60a5fa}</style>
    <h2>Settings</h2><p>{{s.user_name}} - {{s.phone}}</p><p><a href=/friends>Friends/Chat</a> | <a href=/privacy>Privacy</a></p>
    <form method=post><input type=hidden name=action value=delete_my_data><button class=danger>Delete Everything + Chats</button></form><a href=/>Back</a>
    """, s=session)

@app.route("/bot")
@limit("30 per minute")
def bot():
    q=request.args.get("q","").strip()
    if not q: return jsonify({"ask":"/bot?q=Venda"})
    if any(x in q.lower() for x in ["hack","bypass",".json"]): return jsonify({"answer":"Blocked"})
    try: summ=requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{q}", timeout=4).json().get("extract","")[:500]
    except: summ=""
    if not summ: summ=f"KIN: {q}"
    return jso
