import sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): (z, n, {k.upper(): str(x) for k, x in (json.loads(e) if e.startswith("{") else {}).items()}) for v, z, n, e in c.execute("select vnum,zone,name,exits from rooms")}
out = []
for v, (z, n, e) in R.items():
    if z in ("Болото", "Дорога Элендор - Геолант", "Дорога Геолант - Элендор", "Деревня рыбаков"):
        for d, t in e.items():
            if t not in R:
                out.append((z, v, n, d, t))
for o in out:
    print(o)
