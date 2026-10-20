import json
from flask import Flask,request
app=Flask(__name__)
L=json.load(open("languages_8324.json"))
def ans(q):
 q=q.lower()
 for x in L:
  if q in x.get("name","").lower():
   return x["name"]+" ["+x["iso_639_3"]+"]"
 return "Try Zulu - "+str(len(L))+" langs"
@app.route("/",methods=["GET","POST"])
def h():
 a="Ask Zulu..."
 if request.method=="POST":
  a=ans(request.form.get("q",""))
 return f"<h1>KiN {len(L)}</h1><form method=post><input name=q><button>Ask</button></form><pre>{a}</pre>"
app.run(host="0.0.0.0",port=5000)
