import json, os, re, sqlite3, subprocess, sys
os.chdir(r"C:\Users\User\Desktop\Клод мад\mudbot")
env = dict(os.environ, MUD_VIA="bot")
c = sqlite3.connect("data/game.db")
R = {str(v): (z, n, {k.upper(): str(x) for k, x in (json.loads(e) if e.startswith("{") else {}).items()}) for v, z, n, e in c.execute("select vnum,zone,name,exits from rooms")}
def cmd(x):
    r = subprocess.run([sys.executable, "-X", "utf8", "tools/cmd.py", x], env=env, capture_output=True, encoding="utf-8", errors="replace", timeout=300)
    return r.stdout
def cur(out):
    m = re.findall(r"^\[cur\] .*?'vnum': '(\d+)'.*?'name': '([^']*)'", out, re.M)
    return m[-1] if m else ("?", "?")
cand = [v for v, (z, n, e) in R.items() if z == "Дорога Геолант - Элендор" and n == "Дорога" and "W" in e and R.get(e["W"], ("", ""))[1] == "Поле"]
cand += [v for v, (z, n, e) in R.items() if z == "Дорога Геолант - Элендор" and n == "Дорога" and "N" in e and R.get(e["N"], ("", ""))[1] == "Поле" and v not in cand]
print("кандидаты", cand, flush=True)
for v in cand[:14]:
    cmd(f"!go {v}")
    for d in ("запад", "север", "север", "запад", "запад", "север"):
        cmd(d)
    vv, nn = cur(cmd("смотреть"))
    print(v, "→", vv, nn, flush=True)
    if nn == "Дорога" and vv != v:
        print("НАШЛА", v, vv); break
