import sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
for v in ("104040", "104041", "104042", "104043", "104044", "104045", "104046"):
    r = c.execute("select vnum,zone,name,exits from rooms where vnum=?", (v,)).fetchone()
    print(r)
L = [l.strip() for l in open(r"C:\Users\User\Desktop\Тадия\areas\болото.botp", "rb").read().decode("cp1251").split("\n")]
print(L[:34])
