import sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): (z, n, {k.upper(): str(x) for k, x in (json.loads(e) if e.startswith("{") else {}).items()}) for v, z, n, e in c.execute("select vnum,zone,name,exits from rooms")}
seq = [("N", "Поле"), ("N", "Поле"), ("W", "Поле"), ("W", "Поле"), ("N", "Дорога")]
for s in ("107057", "107015"):
    cur, trace = s, [s]
    ok = True
    for d, nm in seq:
        t = R[cur][2].get(d)
        if not t or t not in R or R[t][1] != nm:
            ok = False
            trace.append(f"x{d}")
            break
        cur = t
        trace.append(cur)
    print(s, ok, trace)
