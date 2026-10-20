from flask import Flask, request, redirect, render_template_string
from datetime import datetime
import os
app = Flask(__name__)
posts = []
post_id = [1]
def kin_bot_answer(q):
    q=q.lower()
    if "price" in q or "maize" in q or "market" in q:
        return "Mbombela maize ~R4500/ton. Check morning market."
    if "elder" in q or "story" in q:
        return "Elder: A tree is known by its fruit."
    if "kin" in q:
        return "KIN is Your People First - share text, video, voices."
    if "money" in q or "pay" in q:
        return "KIN Creator Fund: Earn when people like your posts."
    return "Post this in feed so your people can answer too."
HTML_PAGE = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><title>KIN</title><style>body{margin:0;font-family:Arial;background:#f0f2f5}.header{background:#1877f2;color:white;padding:14px;text-align:center;font-size:22px;font-weight:800}.container{max-width:650px;margin:auto;padding:12px}.card{background:white;border-radius:12px;padding:14px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.15)}input,textarea,select{width:100%;padding:11px;border-radius:8px;border:1px solid #ddd;margin-top:8px;box-sizing:border-box}.btn{background:#1877f2;color:white;border:none;padding:11px;border-radius:8px;font-weight:700;width:100%;margin-top:10px}.btn-small{background:#e4e6eb;color:#050505;padding:6px 12px;border-radius:20px;font-size:14px;margin-right:6px;border:none}.badge{display:inline-block;background:#e7f3ff;color:#1877f2;padding:3px 8px;border-radius:20px;font-size:12px;font-weight:700}.small{color:#65676b;font-size:13px}.bot{background:#e7f3ff;border-left:4px solid #1877f2}</style></head><body><div class="header">KIN - Your People First</div><div class="container"><div class="card"><h3>Create Post</h3><form method="POST" action="/post"><input name="name" placeholder="Your name" required><select name="type" required><option value="text">Text Post</option><option value="video">Video link</option><option value="audio">Elder Voice</option></select><textarea name="text" placeholder="What is happening?" required></textarea><button class="btn">Post to KIN</button></form></div><div class="card bot"><h3>Ask KIN Bot</h3><form method="POST" action="/bot"><input name="q" placeholder="Ask about price, elders..." required><button class="btn">Ask Bot</button></form>{% if bot_answer %}<hr><b>You:</b> {{bot_q}}<br><br><b>Bot:</b> {{bot_answer}}{% endif %}</div>{% for p in posts|reverse %}<div class="card"><b>{{p.name}}</b> <span class="badge">{{p.type}}</span> <span class="small">- {{p.time}}</span><p>{{p.text}}</p><form method="POST" action="/like" style="display:inline"><input type="hidden" name="id" value="{{p.id}}"><button class="btn-small">Like ({{p.likes}})</button></form><form method="POST" action="/delete" style="display:inline"><input type="hidden" name="id" value="{{p.id}}"><button class="btn-small">Delete</button></form></div>{% endfor %}</div></body></html>"""
bot_state={"q":"","a":""}
@app.route("/")
def home(): return render_template_string(HTML_PAGE, posts=posts, bot_q=bot_state["q"], bot_answer=bot_state["a"])
@app.route("/post", methods=["POST"])
def do_post():
    name=request.form.get("name","Anon")[:30]
    ptype=request.form.get("type","text")[:10]
    text=request.form.get("text","")[:800]
    if text:
        posts.append({"id":post_id[0],"name":name,"type":ptype,"text":text,"likes":0,"time":datetime.now().strftime("%H:%M %d/%m")})
        post_id[0]+=1
    bot_state["q"]=""; bot_state["a"]=""
    return redirect("/")
@app.route("/like", methods=["POST"])
def do_like():
    try:
        pid=int(request.form.get("id",0))
        for p in posts:
            if p["id"]==pid: p["likes"]+=1
    except: pass
    return redirect("/")
@app.route("/delete", methods=["POST"])
def do_delete():
    try:
        pid=int(request.form.get("id",0))
        global posts
        posts=[p for p in posts if p["id"]!=pid]
    except: pass
    return redirect("/")
@app.route("/bot", methods=["POST"])
def do_bot():
    q=request.form.get("q","")[:200]
    bot_state["q"]=q; bot_state["a"]=kin_bot_answer(q) if q else ""
    return redirect("/")
if __name__=="__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
