import json
from flask import Flask, request
app = Flask(__name__)

SA = [
 ("Venda","ven"),
 ("Sepedi","nso"),
 ("Tsonga","tso"),
 ("Zulu","zul"),
 ("Xhosa","xho"),
 ("Tswana","tsn"),
 ("Sotho","sot"),
 ("Swati","ssw"),
 ("Ndebele","nbl"),
 ("Afrikaans","afr"),
 ("English","eng")
]

try:
    L = json.load(open("languages_8324.json", encoding="utf-8"))
except:
    L = [{"name": n, "iso_639_3": c} for n, c in SA]

def get_country():
    code = request.headers.get("CF-IPCountry", "ZA")
    return "South Africa" if code.upper() == "ZA" else code

def find(q):
    q = (q or "").lower().strip()
    if not q:
        return ""
    for x in L:
        if q in x["name"].lower() or q == x["iso_639_3"]:
            return f"{x['name']} [{x['iso_639_3']}]"
    return f"'{q}' not found"

@app.route("/", methods=["GET", "POST"])
def h():
    country = get_country()
    q = request.values.get("q", "")
    res = find(q)
    btns = ""
    for n, c in SA:
        btns += f"<a href='/?q={c}' style='margin:4px;padding:6px 10px;border:1px solid #ccc;border-radius:20px;text-decoration:none;display:inline-block'>{n}</a>"
    return f"<div style='font-family:sans-serif;padding:15px'><h2>We are in {country}</h2><p>KiN - 8324 langs, identity only, no culture exposed</p><div>{btns}</div><form method='GET' style='margin-top:15px'><input name='q' value='{q}' placeholder='Search Venda Pedi Tsonga...'><button>Search</button></form><p><b>{res or 'Select native or search any'}</b></p></div>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
