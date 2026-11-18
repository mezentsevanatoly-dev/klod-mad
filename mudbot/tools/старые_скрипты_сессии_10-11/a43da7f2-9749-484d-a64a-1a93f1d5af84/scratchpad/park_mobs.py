import sqlite3, re
R = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\парк"
for f in ("парк_mob.csv", "рр_паркV_mob.csv"):
    rows = open(R + "\\" + f, "rb").read().decode("cp1251").split("\r\n")
    print("==", f)
    for r in rows[1:]:
        if r.strip():
            c = r.replace('"', "").split(";")
            print("  ", c[0], "|", c[1][:60], "| ур", c[8], "|", c[14])
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
print("== mob_cards Парк")
for r in c.execute("select name,level,prof,kind,desc from mob_cards where zone like '%Парк%'"):
    print("  ", r[0], r[1], r[2], r[3], (r[4] or "")[:50])
print("== mob_zone/мирные")
try:
    for r in c.execute("select * from mob_zone where zone like '%Парк%' limit 30"):
        print("  ", r)
except Exception as e:
    print(e)
