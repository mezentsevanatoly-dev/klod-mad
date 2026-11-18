import re, json, sqlite3
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {v: json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
N = {v: n for v, n in c.execute("select vnum,name from rooms")}
D = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
L = open(r"C:\Users\User\Desktop\Тадия\claude_game.log", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
S = []
for l in L:
    m = re.match(r"^(\d\d:\d\d:\d\d) ## STEP (\d+) vn=(\S+) cmd=(.*)$", l)
    if m: S.append((int(m.group(2)), m.group(3), m.group(4)))
# последний прогон = после последнего STEP 0/1 ... берём шаги >=197 из хвоста
tail = [s for s in S[-45:]]
for i, (idx, vn, cmd) in enumerate(tail):
    nxt = R.get(vn, {}).get(D.get(cmd, "?"))
    got = tail[i + 1][1] if i + 1 < len(tail) else "?"
    flag = "" if nxt is None or str(nxt) == got or i + 1 == len(tail) else "   <-- БД ждёт %s, пришли в %s (%s)" % (nxt, got, N.get(got))
    print(idx, vn, N.get(vn), cmd, flag)
