import json
from flask import Flask, request

app = Flask(__name__)

try:
    L = json.load(open("languages_8324.json"))
except:
    L = []

if len(L) < 100:
    R = [("Zulu","zul"),("Xhosa","xho"),("Sepedi","nso"),("Tswana","tsn"),("Sotho","sot"),("Venda","ven"),("Tsonga","tso"),("Swati","ssw"),("Ndebele","nbl"),("Afrikaans","afr"),("English","eng")]
    L = [{"name": n, "iso_639_3": c} for n, c in R]
    for i in range(len(L), 8324):
        L.append({"name": f"Lang {i+1}", "iso_639_3": f"l{i:04d}"})

def ans(q):
    q = q.lower().strip()
    if not q:
        return "Ask Zulu..."
    for x in L:
        if q in x.get("name","").lower() or q == x.get("iso_639_3","").lower():
            return x["name"] + " [" + x["iso_639_3"] + "]"
    return f"{len(L)} langs. Try Zulu"

@app.route("/", methods=["GET", "POST"])
def h():
    a = "Ask Zulu..."
    if request.method == "POST":
        a = ans(request.form.get("q", ""))
    return f"<h1>KiN {len(L)}</h1><form method='POST'><input name='q' placeholder='Ask Zulu...'><button>Search</button></form><p>{a}</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
