import sqlite3, json, collections
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
rows = {r[0]: (r[1], r[2], json.loads(r[3] or "{}")) for r in c.execute("select vnum,zone,name,exits from rooms")}
sw = {v for v, r in rows.items() if r[0] == "Болото"}
print("комнат болота в БД:", len(sw))
for v, r in rows.items():
    if r[0] != "Болото":
        for d, t in r[2].items():
            if str(t) in sw:
                print("вход в болото из", v, r[0], r[1], d, "->", t, rows[str(t)][1])
q = collections.deque(["100076"]); p = {"100076": None}
while q:
    v = q.popleft()
    for d, t in rows.get(v, ("", "", {}))[2].items():
        t = str(t)
        if t in rows and t not in p:
            p[t] = (v, d); q.append(t)
reach = [v for v in sw if v in p]
print("достижимо от склада:", len(reach), "из", len(sw))
if reach:
    t = min(reach, key=lambda v: 0)
    # длина пути до ближайшей
    def plen(v):
        n = 0
        while p[v]:
            v = p[v][0]; n += 1
        return n
    best = min(reach, key=plen)
    print("ближайшая:", best, rows[best][1], "длина", plen(best))
print("имена комнат:", sorted({rows[v][1] for v in sw}))
