import sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {r[0]: r for r in c.execute("select vnum,zone,name,exits from rooms")}
print("100076:", R.get("100076"))
sch = [v for v, r in R.items() if r[1] == "Мад школа"]
print("school rooms:", len(sch), sorted(sch)[:5], sorted(sch)[-5:])
for v, r in R.items():
    ex = json.loads(r[3] or "{}")
    for d, t in ex.items():
        if t in R and R[t][1] == "Мад школа" and r[1] != "Мад школа":
            print("вход:", v, r[1], r[2], d, "->", t, R[t][2])
# цепочка от склада
v = "100076"
for _ in range(4):
    r = R.get(v)
    if not r: break
    print(v, r[2], r[3])
    ex = json.loads(r[3] or "{}")
    v = ex.get("S") or ex.get("U") or ""
print(c.execute("select count(*) from mob_cards where zone like '%школ%'").fetchall(), [x[1] for x in c.execute("pragma table_info(mob_cards)")])
