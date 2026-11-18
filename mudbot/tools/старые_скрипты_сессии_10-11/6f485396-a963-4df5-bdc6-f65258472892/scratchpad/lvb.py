import csv, sqlite3
db = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
rows = list(csv.reader(open(r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\бесы\бесы_mob.csv", encoding="cp1251"), delimiter=";"))[1:]
killed = {n.lower() for n, in db.execute("select distinct name from mob_kills where my_level>=25")}
out = []
for r in rows:
    c = db.execute("select level,prof,hp from mob_cards where name=? order by rowid desc limit 1", (r[0],)).fetchone()
    out.append((int(c[0]) if c and str(c[0]).isdigit() else 0, r[0], c[1] if c else "", c[2] if c else "", "убит" if r[0].lower() in killed else "—"))
for o in sorted(out, reverse=True):
    print(o)
