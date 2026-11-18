import json, collections, sqlite3
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
q = collections.deque(["180049"]); p = {"180049": None}
while q:
    v = q.popleft()
    if v == "180154": break
    for d, t in R.get(v, {}).items():
        t = str(t)
        if t not in p and t in R and not (v == "180049" and d == "S"): p[t] = (v, d); q.append(t)
out = []; v = "180154"
while p[v]: pv, d = p[v]; out.append(RU[d]); v = pv
print(";".join(out[::-1]))
L = open(r"C:\Users\User\Desktop\Тадия\areas\леч.botp", "rb").read().decode("cp1251").split("\r\n")
print("индекс строки ехать гео:", next(i for i, l in enumerate(L) if "{ехать гео}" in l))
