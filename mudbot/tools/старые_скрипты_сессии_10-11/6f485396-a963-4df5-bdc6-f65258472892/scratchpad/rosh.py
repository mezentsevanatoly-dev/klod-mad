import sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): (z, n, {k.upper(): str(x) for k, x in (json.loads(e) if e.startswith("{") else {}).items()}) for v, z, n, e in c.execute("select vnum,zone,name,exits from rooms")}
for v, (z, n, e) in R.items():
    if n == "Рощица" and "Дорога" in z:
        print(v, z, e, {d: R.get(t, ("", "?"))[1] for d, t in e.items()})
print([ (v, z, e) for v, (z, n, e) in R.items() if n == "Тропинка"][:8])
