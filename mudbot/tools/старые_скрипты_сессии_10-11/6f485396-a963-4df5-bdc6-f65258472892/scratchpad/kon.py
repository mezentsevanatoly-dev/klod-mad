import sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): (z, n, {k.upper(): str(x) for k, x in (json.loads(e) if e.startswith("{") else {}).items()}) for v, z, n, e in c.execute("select vnum,zone,name,exits from rooms")}
for v, (z, n, e) in R.items():
    for d, t in e.items():
        if t in R and R[t][0] == "Конюшни" and z != "Конюшни":
            print("вход:", v, z, n, d, "->", t, R[t][1])
print([ (v, n) for v, (z, n, e) in R.items() if z == "Конюшни"][:8])
