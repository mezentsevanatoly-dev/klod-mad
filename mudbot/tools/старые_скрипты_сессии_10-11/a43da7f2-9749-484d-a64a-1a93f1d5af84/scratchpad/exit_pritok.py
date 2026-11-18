import json, collections, sqlite3
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {r[0]: json.loads(r[1] or "{}") for r in c.execute("select vnum,exits from rooms")}
N = {r[0]: r[1] for r in c.execute("select vnum,name from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
print("103011:", N.get("103011"), R.get("103011"))
q = collections.deque(["103011"]); p = {"103011": None}
while q:
    v = q.popleft()
    if v == "100011": break
    for d, t in R.get(v, {}).items():
        t = str(t)
        if t not in p and t in R: p[t] = (v, d); q.append(t)
if "100011" in p:
    out = []; v = "100011"
    while p[v]: pv, d = p[v]; out.append((pv, RU[d])); v = pv
    out = out[::-1]
    print("путь 103011 -> 100011:", [(a, b) for a, b in out], [N[a] for a, _ in out])
else:
    print("нет пути в БД")
